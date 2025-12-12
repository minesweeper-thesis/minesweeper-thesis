import uuid
from datetime import datetime, timedelta
from typing import Optional

from backend.core.board import Board
from backend.core.game import *
from backend.core.multi import MultiplayerSession, create_multiplayer_round
from backend.di.dependencies import *
from backend.protocols import SessionNotFound
from backend.repositories.exceptions import *
from backend.services.dto import RoundCountdown
from backend.services.exceptions import *
from backend.services.multi.helpers import calc_round_start_times


class RoundScheduler:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        scheduler: SchedulerDep,
        game_transport_factory: GameTransportFactoryDep,
        board_repo: BoardRepositoryDep,
        notification_system: NotificationSystemDep,
        pending_store: PendingBoardsStoreDep,
    ):
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.game_transport_factory = game_transport_factory

        self.board_repo = board_repo
        self.notification_system = notification_system
        self.pending_store = pending_store

    async def lock_ready(self, session_id: uuid.UUID):
        session = await self.multi_repo.get_session(session_id)
        if session.all_players_ready():
            session.lock_ready()
            await self.multi_repo.save_session(session)

    async def on_board_generated(
        self, session_id: uuid.UUID, generation_id: Optional[uuid.UUID], board: Board
    ):  # todo: board juz istnieje
        try:
            session = await self.multi_repo.get_session(session_id)
        except SessionNotFound:
            await self.board_repo.add_board(board)
            return

        if generation_id is not None:
            await self.pending_store.mark_ready(generation_id, board.id)

        if len(session.rounds) == 0:
            await self._schedule_frist_round_start(session_id, board)
        else:
            await self._add_round_to_session(session_id, board)

    async def _schedule_frist_round_start(self, session_id: uuid.UUID, board: Board):
        session = await self.multi_repo.get_session(session_id)
        await self._add_round_to_session(session.id, board)

        await self.schedule_start(session, immediately=True)

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

        await self._send_events(session)

        if session.is_over():
            transport = self.game_transport_factory.create(session_id)
            for user_id in session.player_ids:
                await transport.close(user_id)

        await self.multi_repo.save_session(session)

    async def start_round(
        self, session_id: uuid.UUID, start_at: datetime, immediately: bool = False
    ):
        session = await self.multi_repo.get_session(session_id)
        if not immediately and not session.all_players_ready():
            return

        end_at = start_at + timedelta(seconds=session.game_config.max_round_time)

        session.start_next_round(start_at)

        await self._send_events(session)

        self.scheduler.schedule(
            self.end_round, end_at, session_id=session_id
        )  # todo: save job id

        await self.multi_repo.save_session(session)

    async def _send_countdown(
        self,
        session: MultiplayerSession,
        round_start_time: datetime,
        countdown_to: datetime,
        in_game: bool = False,
    ):
        if in_game:
            transport = self.game_transport_factory.create(session.id)
            sender = transport.send
        else:
            sender = self.notification_system.notify

        for user_id in session.player_ids:
            await sender(
                user_id,
                RoundCountdown(
                    session.id,
                    0,
                    countdown_to,
                    round_start_time,
                    session._next_round.board.start_field,
                ),
            )

    async def _send_events(self, session: MultiplayerSession):
        transport = self.game_transport_factory.create(session.id)
        for user_id, events in session.consume_events().items():
            for event in events:
                await transport.send(user_id, event)

    async def schedule_start(
        self,
        session: MultiplayerSession,
        immediately=False,
    ):
        countdown_to, start_at = calc_round_start_times()

        in_game = not immediately
        await self._send_countdown(session, start_at, countdown_to, in_game=in_game)

        self.scheduler.schedule(
            self.lock_ready,
            countdown_to,
            session_id=session.id,
        )

        self.scheduler.schedule(
            self.start_round,
            start_at,
            start_at=start_at,
            session_id=session.id,
            immediately=immediately,
        )  # todo: save job id


__all__ = ["RoundScheduler"]
