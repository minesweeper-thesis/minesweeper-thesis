import logging
import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends

from backend.core.game import *
from backend.core.multi import MultiplayerSession
from backend.di.dependencies import *
from backend.services.dto import (
    RoundCountdown,
    RoundEnd,
    RoundSchedule,
    RoundStart,
    SessionOver,
)
from backend.services.exceptions import *
from backend.services.multi.constants import COUNTDOWN_DELAY, START_DELAY
from backend.services.multi.session_renewer import SessionRenewer

logger = logging.getLogger(__name__)


class RoundScheduler:
    def __init__(
        self,
        scheduler: SchedulerDep,
        session_lock: SessionLockDep,
        board_repo: BoardRepositoryDep,
        lobby_repo: LobbyRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        pending_store: PendingBoardsStoreDep,
        session_runtime_store: SessionRuntimeStoreDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
        session_renewer: Annotated[SessionRenewer, Depends()],
    ):
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.lobby_transport_factory = lobby_transport_factory
        self.lobby_repo = lobby_repo
        self.board_repo = board_repo
        self.pending_store = pending_store
        self.session_runtime_store = session_runtime_store
        self.session_lock = session_lock
        self.session_renewer = session_renewer

    async def _lock_ready_and_schedule_start(
        self, session_id: uuid.UUID, start_at: datetime
    ):
        logger.debug(
            f"_lock_ready_and_schedule_start(session_id={session_id}, start_at={start_at})"
        )
        should_schedule = False

        session = await self.multi_repo.get_session(session_id)
        async with self.session_lock.acquire(session_id):
            logger.debug(
                f"Session {session_id} acquired for locking round {session.next_round_index}"
            )
            if not session.all_players_ready():
                return

            session.lock_ready()
            board_id = await self.session_runtime_store.get_ready_board(session_id)
            assert board_id is not None
            board = await self.board_repo.get_board_by_id(board_id)
            session.add_next_round(start_at, board, session.player_ids)
            await self.multi_repo.save_session(session)
            should_schedule = True

        if should_schedule:
            self.scheduler.schedule(
                self._start_current_round,
                start_at,
                session_id=session_id,
                start_at=start_at,
            )

    async def _end_round(self, session_id: uuid.UUID, round_index: int):
        logger.debug(f"_end_round(session_id={session_id}, round_index={round_index})")
        session_over = False

        await self.session_runtime_store.delete_round_schedule(session_id)
        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)

            if session.rounds[round_index].ended_before_timeout:
                logger.warning(
                    f"Round {round_index} in session {session_id} is already ended"
                )
                return

            session.timeout_round(round_index)

            events_by_user = session.consume_events()
            session_over = session.is_over()

            await self.multi_repo.save_session(session)

        transport = self.lobby_transport_factory.get(session.lobby_id)
        await transport.send_many(events_by_user)
        await transport.broadcast(
            RoundEnd(
                session_id=session.id,
                round_index=session.current_round_index,
                scoreboard=session.rounds[round_index].scoreboard,
            )
        )

        if session_over:
            await self.session_renewer.renew_session(session.lobby_id)
            await transport.broadcast(
                SessionOver(session_id=session.id, scoreboard=session.scoreboard)
            )

    async def _start_current_round(self, session_id: uuid.UUID, start_at: datetime):
        logger.debug(f"_start_round(session_id={session_id})")

        session = await self.multi_repo.get_session(session_id)
        lobby = await self.lobby_repo.get_lobby(session.lobby_id)
        board_id = session._current_round.board_id
        board = await self.board_repo.get_board_by_id(board_id)

        transport = self.lobby_transport_factory.get(lobby.id)
        await transport.broadcast(
            RoundStart(
                session_id=session.id,
                round_index=session.current_round_index,
                start_at=session._current_round._start_at,
                end_at=session._current_round._end_at,
                start_field=board.start_field,
            ),
        )

        end_at = start_at + timedelta(seconds=session.game_config.max_round_time)
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
    ):
        board_id = await self.session_runtime_store.peek_ready_board(session.id)
        assert board_id is not None
        board = await self.board_repo.get_board_by_id(board_id)

        transport = self.lobby_transport_factory.get(session.lobby_id)
        await transport.broadcast(
            RoundCountdown(
                session.id,
                session.next_round_index,
                countdown_to,
                round_start_time,
                board.start_field,
            ),
        )

    async def schedule_start(self, session: MultiplayerSession):
        logger.debug(f"schedule_start(session_id={session.id})")
        countdown_to, start_at = calc_round_start_times()
        end_at = start_at + timedelta(seconds=session.game_config.max_round_time)

        schedule_ttl = int((end_at - datetime.now()).total_seconds()) + 10
        await self.session_runtime_store.set_round_schedule(
            session.id,
            RoundSchedule(countdown_to, start_at, end_at),
            ttl=schedule_ttl,
        )

        await self._send_countdown(session, start_at, countdown_to)

        lock_job_id = self.scheduler.schedule(
            self._lock_ready_and_schedule_start,
            countdown_to,
            session_id=session.id,
            start_at=start_at,
        )
        await self.session_runtime_store.set_lock_job_id(session.id, lock_job_id)

    async def cancel_start(self, session_id: uuid.UUID):
        logger.debug(f"cancel_start(session_id={session_id})")

        lock_job_id = await self.session_runtime_store.get_lock_job_id(session_id)
        if lock_job_id is not None:
            self.scheduler.cancel(lock_job_id)

        schedule = await self.session_runtime_store.get_round_schedule(session_id)
        if schedule:
            await self.session_runtime_store.delete_round_schedule(session_id)


def calc_round_start_times():
    countdown_to = datetime.now() + COUNTDOWN_DELAY
    start_at = countdown_to + START_DELAY
    return countdown_to, start_at


__all__ = ["RoundScheduler"]
