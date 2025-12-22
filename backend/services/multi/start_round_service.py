import logging
import uuid
from typing import Annotated

from fastapi import BackgroundTasks, Depends

logger = logging.getLogger(__name__)

from backend.core.game import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.di.session_lock import SessionLockDep
from backend.services.dto import *
from backend.services.exceptions import *
from backend.services.multi.components import (
    PendingBoardWaiter,
    RoundReadinessNotifier,
    SessionBoardsPreparer,
)
from backend.services.multi.round_scheduler import RoundScheduler


class StartRoundService:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystemDep,
        game_transport_factory: GameTransportFactoryDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
        readiness_notifier: Annotated[RoundReadinessNotifier, Depends()],
        pending_board_waiter: Annotated[PendingBoardWaiter, Depends()],
        boards_preparer: Annotated[SessionBoardsPreparer, Depends()],
        pending_store: PendingBoardsStoreDep,
        session_lock: SessionLockDep,
    ):
        self.multi_repo = multi_repo
        self.background_tasks = background_tasks
        self.game_transport_factory = game_transport_factory
        self.round_scheduler = round_scheduler
        self.pending_board_waiter = pending_board_waiter
        self.boards_preparer = boards_preparer
        self.notification_system = notification_system
        self.readiness_notifier = readiness_notifier
        self.session_lock = session_lock
        self.pending_store = pending_store

    def _ensure_user_in_session(self, session: MultiplayerSession, user: User):
        if user.id not in session.player_ids:
            raise UserNotInSession()

        if session.is_over():
            raise SessionAlreadyOver()

    async def toggle_user_ready(self, session_id: uuid.UUID, user: User):
        logger.debug(f"User {user.id} toggling ready status in session {session_id}")
        session = await self.multi_repo.get_session(session_id)
        self._ensure_user_in_session(session, user)
        if session.is_user_ready(user.id):
            await self.cancel_user_ready(session_id, user)
        else:
            await self.set_user_ready(session_id, user)

    async def cancel_user_ready(self, session_id: uuid.UUID, user: User):
        logger.debug(f"User {user.id} cancelling ready status in session {session_id}")
        should_notify = False

        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)
            self._ensure_user_in_session(session, user)

            if session.is_user_ready(user.id) and not session.ready_locked:
                session.cancel_ready(user.id)
                await self.multi_repo.save_session(session)
                should_notify = True

        if should_notify:
            await self.readiness_notifier.send_user_not_ready(
                self.notification_system.notify, session, user
            )

    async def set_user_ready(self, session_id: uuid.UUID, user: User):
        logger.debug(f"User {user.id} setting ready status in session {session_id}")
        should_notify = False
        all_ready = False

        async with self.session_lock.acquire(session_id):
            session = await self.multi_repo.get_session(session_id)
            self._ensure_user_in_session(session, user)

            if not session.is_user_ready(user.id) and not session.ready_locked:
                session.set_ready(user.id)
                await self.multi_repo.save_session(session)
                should_notify = True
                all_ready = session.all_players_ready()

        if should_notify:
            await self.readiness_notifier.send_user_ready(
                self.notification_system.notify, session, user
            )

            if all_ready:
                await self._on_all_ready(session)

    async def _on_all_ready(self, session: MultiplayerSession):
        logger.info(f"All players ready in session {session.id}, starting round")
        transport = self.game_transport_factory.create(session.id)

        if session.current_round_index == -1:
            sender = self.notification_system.notify
        else:
            sender = transport.send
        await self.readiness_notifier.send_round_ready(sender, session)

        is_pending = await self.pending_store.get_pending_round(session.id, 0)

        if len(session.rounds) == 0 and not is_pending:
            logger.info(f"Preparing boards for first round in session {session.id}")
            await self.boards_preparer.prepare(session)
            session = await self.multi_repo.get_session(session.id)

        is_not_first_round = session.current_round_index != -1

        if session.is_next_round_available:
            logger.info(f"Scheduling start of next round in session {session.id}")
            await self.round_scheduler.schedule_start(
                session, in_game=is_not_first_round
            )
        else:
            logger.info(
                f"No next round available in session {session.id}, waiting for boards"
            )
            self.background_tasks.add_task(
                self.pending_board_waiter.wait_and_schedule_next_round, session.id
            )


__all__ = ["StartRoundService"]
