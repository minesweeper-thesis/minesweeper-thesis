import logging
import uuid
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends

from backend.core.game import *
from backend.core.multi import MultiplayerSession
from backend.di.dependencies import *
from backend.services.dto import RoundCountdown, RoundSchedule
from backend.services.exceptions import *
from backend.services.multi.constants import COUNTDOWN_DELAY, START_DELAY
from backend.services.multi.session_renewer import SessionRenewer

logger = logging.getLogger(__name__)


class RoundScheduler:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        scheduler: SchedulerDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
        board_repo: BoardRepositoryDep,
        pending_store: PendingBoardsStoreDep,
        session_runtime_store: SessionRuntimeStoreDep,
        session_lock: SessionLockDep,
        session_renewer: Annotated[SessionRenewer, Depends()],
    ):
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.lobby_transport_factory = lobby_transport_factory

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

        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)
            logger.debug(
                f"Session {session_id} acquired for locking round {session.current_round_index + 1}"
            )
            if session.all_players_ready():
                session.lock_ready()
                session.prepare_next_round(start_at)
                await self.multi_repo.save_session(session)
                should_schedule = True

        if should_schedule:
            self.scheduler.schedule(
                self._start_round,
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

            if not session._current_round.all_gameplays_finished():
                session.end_round(round_index)

            events_by_user = session.consume_events()
            session_over = session.is_over()

            await self.multi_repo.save_session(session)

        await self._publish_events(session.lobby_id, events_by_user)

        if session_over:
            transport = self.lobby_transport_factory.get(session.lobby_id)
            for user_id in session.player_ids:
                await transport.close(user_id)

            await self.session_renewer.renew_session(session.lobby_id)

    async def _start_round(self, session_id: uuid.UUID, start_at: datetime):
        logger.debug(f"_start_round(session_id={session_id})")

        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)
            session.start_next_round()

            events_by_user = session.consume_events()
            await self.multi_repo.save_session(session)

        await self._publish_events(session.lobby_id, events_by_user)

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
        transport = self.lobby_transport_factory.get(session.lobby_id)
        sender = transport.send

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
        self, lobby_id: uuid.UUID, events_by_user: dict[uuid.UUID, list[Any]]
    ):
        transport = self.lobby_transport_factory.get(lobby_id)
        for user_id, events in events_by_user.items():
            for event in events:
                await transport.send(user_id, event)

    async def schedule_start(self, session: MultiplayerSession):
        logger.debug(f"schedule_start(session_id={session.id})")
        countdown_to, start_at = calc_round_start_times()
        end_at = start_at + timedelta(seconds=session.game_config.max_round_time)

        await self.session_runtime_store.set_round_schedule(
            session.id, RoundSchedule(countdown_to, start_at, end_at)
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
        can_cancel = False

        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)
            if not session.ready_locked:
                can_cancel = True
                session.next_round.prepare(None, {})
                await self.multi_repo.save_session(session)

        if can_cancel:
            schedule = await self.session_runtime_store.get_round_schedule(session_id)
            if schedule is not None:
                await self.session_runtime_store.delete_round_schedule(session_id)

            lock_job_id = await self.session_runtime_store.get_lock_job_id(session_id)
            if lock_job_id is not None:
                self.scheduler.cancel(lock_job_id)


def calc_round_start_times():
    countdown_to = datetime.now() + COUNTDOWN_DELAY
    start_at = countdown_to + START_DELAY
    return countdown_to, start_at


__all__ = ["RoundScheduler"]
