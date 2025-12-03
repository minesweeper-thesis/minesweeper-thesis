import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Annotated, Any, Awaitable

from fastapi import BackgroundTasks, Depends

from backend import protocols, repositories
from backend.core.board import Board, GenerationSettings
from backend.core.game import *
from backend.core.lobby import create_session
from backend.core.multi.config import GameConfig
from backend.core.multi.round import RoundEnd, RoundStart
from backend.core.multi.session import (
    Clock,
    RoundStartAwaiting,
    RoundStartCanceled,
    SessionOver,
)
from backend.core.user import User
from backend.lib.board_generator import LocalBoardGenerator
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.lib.pending_boards import get_pending_boards_store
from backend.lib.scheduler import get_scheduler
from backend.lib.websocket_game_transport import WebSocketGameTransport
from backend.protocols.pending_boards import PendingBoardMetadata
from backend.repositories.exceptions import *
from backend.services.dto import GameActionResult
from backend.services.exceptions import *
from backend.services.multi.round_orchiestrator import RoundOrchestrator

MultiplayerRepository = Annotated[
    protocols.MultiplayerRepository, Depends(repositories.MultiplayerRepository)
]
BoardRepository = Annotated[
    protocols.BoardRepository, Depends(repositories.BoardRepository)
]
LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]
Scheduler = Annotated[protocols.Scheduler, Depends(get_scheduler)]
GameTransport = Annotated[
    protocols.GameTransport, Depends(lambda: WebSocketGameTransport())
]
BoardGenerator = Annotated[protocols.BoardGenerator, Depends(LocalBoardGenerator)]
PendingGameplaysStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]


type MultiplayerResult = RoundStart | RoundEnd | RoundStartAwaiting | RoundStartCanceled | SessionOver | GameActionResult


type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


ROUND_START_DELAY = timedelta(seconds=10)


class ClockImpl(Clock):
    def now(self) -> datetime:
        return datetime.now()


class CreateMultiplayerSessionUseCase:
    def __init__(
        self,
        board_repo: BoardRepository,
        lobby_repo: LobbyRepository,
        multi_repo: MultiplayerRepository,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystem,
        scheduler: Scheduler,
        game_transport: GameTransport,
        board_generator: BoardGenerator,
        pending_store: PendingGameplaysStore,
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport = game_transport
        self.board_generator = board_generator
        self.pending_store = pending_store

    async def set_user_ready_in_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        lobby.set_user_ready(user)
        self.lobby_repo.save_lobby(lobby)

        if lobby.all_users_ready():
            start_at = datetime.now() + ROUND_START_DELAY

            session_id = uuid.uuid4()
            # pending_sessions_store.add(session_id, [u.id for u in lobby.users])

            self.scheduler.schedule(
                self._create_game_session,
                start_at,
                session_id=session_id,
                lobby_id=lobby.id,
                start_at=start_at,
            )

            event = RoundStartAwaiting(
                session_id=session_id, round=0, start_at=start_at
            )
            for lobby_user in lobby.users:
                await self.notification_system.notify(lobby_user.id, event)

    async def _create_game_session(
        self,
        session_id: uuid.UUID,
        lobby_id: uuid.UUID,
        start_at: datetime,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if lobby.all_users_ready():
            lobby.reset_ready_for_new_session()
            self.session = await create_session(session_id, lobby, ClockImpl())

            # for _ in range(self.session.rounds_number):

            end_at = start_at + timedelta(seconds=self.session.max_round_time)
            self.session.start_next_round()

            await self.multi_repo.save_session(self.session)

            # pending_sessions_store.mark_ready(session_id)

            orchestrator = RoundOrchestrator(
                self.session,
                self.multi_repo,
                self.scheduler,
                self.game_transport,
            )

            for event in self.session.get_events():
                for user_id in self.session.player_ids:
                    await self.game_transport.send(user_id, event)

            self.session_id = session_id
            self.scheduler.schedule(orchestrator.end_round, end_at)

    async def generate_round(
        self,
        session_id: uuid.UUID,
        game_config: GameConfig,
        round_index: int,
    ):
        async def on_board_generated(generation_id: uuid.UUID, board: Board):
            try:
                existing_board = await self.board_repo.get_board(
                    board.difficulty_level, board.minefields
                )
                board = existing_board
            except BoardNotFound:
                await self.board_repo.add_board(board)

            await self.pending_store.mark_ready(generation_id)

        settings = GenerationSettings(
            type=game_config.generator_type,
            difficulty_level=game_config.difficulty_level,
            settings=game_config.generator_settings,
        )

        generation_id = await self.board_generator.generate_board(
            settings, on_completed=on_board_generated
        )

        await self.pending_store.create_pending(
            generation_id=generation_id,
            metadata=PendingBoardMetadata(
                generation_settings=settings,
                difficulty_level=game_config.difficulty_level,
                mode=game_config.game_mode,
                session_id=session_id,
                round_index=round_index,
            ),
            ttl_seconds=180,
        )


__all__ = ["CreateMultiplayerSessionUseCase"]
