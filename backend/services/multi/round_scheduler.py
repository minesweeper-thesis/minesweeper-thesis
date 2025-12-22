import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

from backend.core.board import Board
from backend.core.game import *
from backend.core.multi import MultiplayerSession, create_multiplayer_round
from backend.di.dependencies import *
from backend.di.session_lock import SessionLockDep
from backend.protocols import SessionNotFound
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
        session_lock: SessionLockDep,
    ):
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.game_transport_factory = game_transport_factory

        self.board_repo = board_repo
        self.notification_system = notification_system
        self.pending_store = pending_store
        self.session_lock = session_lock

    async def _lock_ready_and_schedule_start(
        self, session_id: uuid.UUID, start_at: datetime
    ):
        logger.debug(f"Locking ready and scheduling start for session {session_id}")
        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)
            if session.all_players_ready():
                session.lock_ready()
                await self.multi_repo.save_session(session)

        self.scheduler.schedule(
            self.start_round,
            start_at,
            session_id=session_id,
            start_at=start_at,
        )

    async def on_board_generated(
        self, session_id: uuid.UUID, generation_id: Optional[uuid.UUID], board: Board
    ):  # todo: board juz istnieje
        logger.debug(f"Board generated for session {session_id}")
        try:
            await self.multi_repo.get_session(session_id)
        except SessionNotFound:
            await self.board_repo.add_board(board)
            return

        if generation_id is not None:
            await self.pending_store.mark_ready(generation_id, board.id)

        await self._add_round_to_session(session_id, board)

    async def _add_round_to_session(self, session_id: uuid.UUID, board: Board):
        logger.debug(f"Adding round with board {board.id} to session {session_id}")
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

    async def _end_round(self, session_id: uuid.UUID, round_index: int):
        logger.debug(f"Ending round {round_index} in session {session_id}")
        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)

            session.end_round(round_index)

            events_by_user = session.consume_events()
            session_over = session.is_over()

            await self.multi_repo.save_session(session)

            await self._publish_events(session.id, events_by_user)

            if session_over:
                transport = self.game_transport_factory.create(session_id)
                for user_id in session.player_ids:
                    await transport.close(user_id)

    async def start_round(self, session_id: uuid.UUID, start_at: datetime):
        logger.debug(f"Starting round in session {session_id}")
        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)
            if not session.all_players_ready():
                return

            end_at = start_at + timedelta(seconds=session.game_config.max_round_time)

            session.start_next_round(start_at)

            events_by_user = session.consume_events()

            await self.multi_repo.save_session(session)

            await self._publish_events(session.id, events_by_user)

            self.scheduler.schedule(
                self._end_round,
                end_at,
                session_id=session_id,
                round_index=session.current_round_index,
            )

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
                    session.current_round_index + 1,
                    countdown_to,
                    round_start_time,
                    session.next_round.board.start_field,
                ),
            )

    async def _publish_events(
        self, session_id: uuid.UUID, events_by_user: dict[uuid.UUID, list[Any]]
    ):
        transport = self.game_transport_factory.create(session_id)
        for user_id, events in events_by_user.items():
            for event in events:
                await transport.send(user_id, event)

    async def schedule_start(self, session: MultiplayerSession, in_game=True):
        logger.debug(
            f"Scheduling start of round in session {session.id}, in_game={in_game}"
        )
        countdown_to, start_at = calc_round_start_times()

        await self._send_countdown(session, start_at, countdown_to, in_game=in_game)

        self.scheduler.schedule(
            self._lock_ready_and_schedule_start,
            countdown_to,
            session_id=session.id,
            start_at=start_at,
        )


__all__ = ["RoundScheduler"]
