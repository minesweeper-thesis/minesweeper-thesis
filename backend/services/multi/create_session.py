import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Annotated, Any, Awaitable, Optional

from fastapi import Depends

from backend import protocols, repositories
from backend.core.board import Board
from backend.core.game import *
from backend.core.lobby import create_session
from backend.core.multi.config import GameConfig
from backend.core.multi.events import AllReady, RoundStartAwaiting
from backend.core.multi.round import create_multiplayer_round
from backend.core.multi.session import Clock
from backend.core.user import User
from backend.lib.board_generator import LocalBoardGenerator
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.lib.pending_boards import get_pending_boards_store
from backend.lib.scheduler import get_scheduler
from backend.lib.websocket_game_transport import WebSocketGameTransport
from backend.protocols.pending_boards import PendingBoardMetadata
from backend.repositories.exceptions import *
from backend.services.exceptions import *
from backend.services.multi.round_orchestrator import RoundOrchestrator

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
PendingBoardsStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]


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
        notification_system: NotificationSystem,
        scheduler: Scheduler,
        game_transport: GameTransport,
        board_generator: BoardGenerator,
        pending_store: PendingBoardsStore,
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport = game_transport
        self.board_generator = board_generator
        self.pending_store = pending_store

        self.orchestrator = RoundOrchestrator(
            self.multi_repo,
            self.scheduler,
            self.game_transport,
        )

    async def cancel_user_ready_in_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        lobby.set_user_not_ready(user)
        self.lobby_repo.save_lobby(lobby)

    async def set_user_ready_in_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        lobby.set_user_ready(user)
        self.lobby_repo.save_lobby(lobby)

        if lobby.all_users_ready():
            lobby_session = await self.multi_repo.get_pending_for_lobby(lobby.id)

            if lobby_session is not None:
                if lobby_session.game_config == lobby.game_config:
                    session = lobby_session
                else:
                    # todo cancel tasks
                    session_id = uuid.uuid4()
                    session = await create_session(session_id, lobby, ClockImpl())
            else:
                session_id = uuid.uuid4()
                session = await create_session(session_id, lobby, ClockImpl())

            self.session_id = session.id
            await self.multi_repo.save_pending(session)

            for user in lobby.users:
                await self.notification_system.notify(user.id, AllReady(session.id, 0))

            await self.generate_boards()

    async def on_board_generated(
        self, generation_id: Optional[uuid.UUID], board: Board
    ):
        session = await self.multi_repo.get_session(self.session_id)
        # todo: return if session not found

        # todo: dodawac board do bazy (tylko raz)

        if generation_id is not None:
            await self.pending_store.mark_ready(generation_id)

        print("generated", len(session.rounds))

        if len(session.rounds) == 0:
            await self.schedule_frist_round_start(board)
        else:
            await self.add_round_to_session(board)

    async def schedule_frist_round_start(self, board: Board):
        session = await self.multi_repo.get_session(self.session_id)
        await self.add_round_to_session(board)

        round_start_time = datetime.now() + ROUND_START_DELAY

        for user_id in session.player_ids:
            await self.notification_system.notify(
                user_id, RoundStartAwaiting(session.id, 0, round_start_time)
            )

        self.scheduler.schedule(
            self.orchestrator.start_round,
            round_start_time,
            start_at=round_start_time,
            session=session,
            first_round=True,
        )  # todo: save job id

    async def add_round_to_session(self, board: Board):
        session = await self.multi_repo.get_session(self.session_id)

        lobby = self.lobby_repo.get_lobby(session.lobby_id)

        round_time = timedelta(seconds=lobby.game_config.max_round_time)
        round = await create_multiplayer_round(
            session_id=session.id,
            round_index=len(session.rounds) + 1,
            round_time=round_time,
            board=board,
            player_ids=session.player_ids,
            mode=lobby.game_config.game_mode,
            clock=ClockImpl(),
        )

        session.add_round(round)
        await self.multi_repo.save_session(session)

    async def generate_boards(self):
        session = await self.multi_repo.get_session(self.session_id)
        lobby = self.lobby_repo.get_lobby(session.lobby_id)
        to_generate = session.rounds_number - len(session.rounds)

        print("to generate", to_generate)

        for round_index in range(to_generate):
            game_config = lobby.game_config
            await self.start_generation(game_config, round_index)

    async def start_generation(self, game_config: GameConfig, round_index: int):
        session = await self.multi_repo.get_session(self.session_id)
        lobby = self.lobby_repo.get_lobby(session.lobby_id)

        board = await self._get_unsolved_or_generate_board(
            game_config, lobby.users, round_index
        )

        if board is not None:
            await self.on_board_generated(None, board)

    async def _get_unsolved_or_generate_board(
        self, game_config: GameConfig, users: list[User], round_index: int
    ) -> Optional[Board]:
        try:
            return await self.board_repo.get_unsolved_board(
                game_config.difficulty_level,
                generation_settings=game_config.generation_settings,
                user_ids=[user.id for user in users],
            )

        except UnsolvedBoardNotFound:
            await self._generate_board(game_config, round_index)
            return None

    async def _generate_board(self, game_config: GameConfig, round_index: int):
        generation_id = await self.board_generator.generate_board(
            game_config.generation_settings, on_completed=self.on_board_generated
        )

        await self.pending_store.create_pending(
            generation_id,
            PendingBoardMetadata(
                generation_settings=game_config.generation_settings,
                difficulty_level=game_config.difficulty_level,
                mode=game_config.game_mode,
                session_id=self.session_id,
                round_index=round_index,
            ),
            24 * 3600,
        )


__all__ = ["CreateMultiplayerSessionUseCase"]
