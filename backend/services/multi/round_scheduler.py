import uuid
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends

from backend import protocols, repositories
from backend.core.board import Board
from backend.core.game import *
from backend.core.multi import create_multiplayer_round
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.lib.pending_boards import get_pending_boards_store
from backend.lib.scheduler import get_scheduler
from backend.lib.websocket_game_transport import WebSocketGameTransport
from backend.protocols.multiplayer_repo_protocol import SessionNotFound
from backend.repositories.exceptions import *
from backend.services.dto import RoundCountdown
from backend.services.exceptions import *

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
PendingBoardsStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]

ROUND_START_DELAY = timedelta(seconds=5)


class RoundScheduler:
    def __init__(
        self,
        multi_repo: MultiplayerRepository,
        scheduler: Scheduler,
        game_transport: GameTransport,
        board_repo: BoardRepository,
        lobby_repo: LobbyRepository,
        notification_system: NotificationSystem,
        pending_store: PendingBoardsStore,
    ):
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.game_transport = game_transport

        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.notification_system = notification_system
        self.pending_store = pending_store

    async def lock_ready(self, session_id: uuid.UUID):
        session = await self.multi_repo.get_session(session_id)
        session.lock_ready()
        await self.multi_repo.save_session(session)

    async def on_board_generated(
        self, session_id: uuid.UUID, generation_id: Optional[uuid.UUID], board: Board
    ):
        try:
            session = await self.multi_repo.get_session(session_id)
        except SessionNotFound:
            await self.board_repo.add_board(board)
            return

        if generation_id is not None:
            await self.pending_store.mark_ready(generation_id)

        if len(session.rounds) == 0:
            await self._schedule_frist_round_start(session_id, board)
        else:
            await self._add_round_to_session(session_id, board)

    async def _schedule_frist_round_start(self, session_id: uuid.UUID, board: Board):
        session = await self.multi_repo.get_session(session_id)
        await self._add_round_to_session(session.id, board)

        countdown_to = datetime.now() + ROUND_START_DELAY
        round_start_time = countdown_to + ROUND_START_DELAY

        for user_id in session.player_ids:
            await self.notification_system.notify(
                user_id,
                RoundCountdown(
                    session_id,
                    0,
                    countdown_to,
                    round_start_time,
                    session.rounds[0].board.start_field,
                ),
            )

        self.scheduler.schedule(
            self.lock_ready,
            countdown_to,
            session_id=session.id,
        )

        self.scheduler.schedule(
            self.start_round,
            round_start_time,
            start_at=round_start_time,
            session_id=session.id,
            first_round=True,
        )  # todo: save job id

    async def _add_round_to_session(self, session_id: uuid.UUID, board: Board):
        session = await self.multi_repo.get_session(session_id)

        round_time = timedelta(seconds=session.game_config.max_round_time)
        round = await create_multiplayer_round(
            session_id=session.id,
            round_index=len(session.rounds),
            round_time=round_time,
            board=board,
            player_ids=session.player_ids,
            mode=session.game_config.game_mode,
        )

        session.add_round(round)
        await self.multi_repo.save_session(session)

    async def end_round(self, session_id: uuid.UUID):
        session = await self.multi_repo.get_session(session_id)
        # todo: lock z handle game action

        session.end_current_round()

        for user_id, events in session.consume_events().items():
            for event in events:
                await self.game_transport.send(user_id, event)

        if session.is_session_over():
            await self.game_transport.close_all()

        await self.multi_repo.save_session(session)

    async def start_round(
        self, session_id: uuid.UUID, start_at: datetime, first_round: bool = False
    ):
        session = await self.multi_repo.get_session(session_id)
        if not first_round and not session.all_players_ready():
            return

        end_at = start_at + timedelta(seconds=session.max_round_time)

        session.start_next_round(start_at)

        for user_id, events in session.consume_events().items():
            for event in events:
                await self.game_transport.send(user_id, event)

        self.scheduler.schedule(
            self.end_round, end_at, session_id=session_id
        )  # todo: save job id

        await self.multi_repo.save_session(session)


__all__ = ["RoundScheduler"]
