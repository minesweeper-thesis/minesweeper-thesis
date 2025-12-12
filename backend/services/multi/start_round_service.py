import logging
import uuid
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends

logger = logging.getLogger(__name__)

from backend.core.game import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.repositories.exceptions import *
from backend.services.dto import *
from backend.services.exceptions import *
from backend.services.multi.components import RoundReadinessNotifier
from backend.services.multi.round_scheduler import RoundScheduler


class StartRoundService:
    def __init__(
        self,
        board_repo: BoardRepositoryDep,
        lobby_repo: LobbyRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystemDep,
        scheduler: SchedulerDep,
        game_transport_factory: GameTransportFactoryDep,
        pending_store: PendingBoardsStoreDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
        readiness_notifier: Annotated[RoundReadinessNotifier, Depends()],
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport_factory = game_transport_factory
        self.pending_store = pending_store
        self.round_scheduler = round_scheduler
        self.readiness_notifier = readiness_notifier

        self.messages: list[tuple[uuid.UUID, Any]] = []

    def _ensure_user_in_session(self, session: MultiplayerSession, user: User):
        if user.id not in session.player_ids:
            raise PermissionError("User is not part of this session")

        if session.is_over():
            raise ValueError("Session is already over")

    async def toggle_user_ready(self, session_id: uuid.UUID, user: User):
        logger.debug(f"User {user.id} toggling ready status in session {session_id}")
        session = await self.multi_repo.get_session(session_id)
        self._ensure_user_in_session(session, user)
        if session.is_user_ready(user):
            await self._cancel_user_ready(session, user)
        else:
            await self.set_user_ready(session_id, user)

    async def cancel_user_ready(self, session_id: uuid.UUID, user: User):
        session = await self.multi_repo.get_session(session_id)
        self._ensure_user_in_session(session, user)
        await self._cancel_user_ready(session, user)

    async def _cancel_user_ready(self, session: MultiplayerSession, user: User):
        self._ensure_user_in_session(session, user)

        if session.ready_locked:
            return

        if not session.is_user_ready(user):
            return

        session.cancel_ready(user.id)

        await self.multi_repo.save_session(session)

        await self.readiness_notifier.send_user_not_ready(
            self.notification_system.notify, session, user
        )

    async def set_user_ready(self, session_id: uuid.UUID, user: User):
        session = await self.multi_repo.get_session(session_id)

        self._ensure_user_in_session(session, user)

        if session.ready_locked:
            return

        if session.is_user_ready(user):
            return

        session.set_ready(user.id)

        transport = self.game_transport_factory.create(session_id)
        await self.readiness_notifier.send_user_ready(
            self.notification_system.notify, session, user
        )

        if session.all_players_ready():
            logger.info(f"All players ready in session {session_id}, starting round")
            await self.readiness_notifier.send_round_ready(transport.send, session)

            if session.is_next_round_available:
                await self.round_scheduler.schedule_start(session)
            else:
                self.background_tasks.add_task(
                    self._wait_for_generation_and_start_round, session
                )

        await self.multi_repo.save_session(session)

    async def _wait_for_generation_and_start_round(self, session: MultiplayerSession):
        next_round_index = session.current_round_index + 1

        pending = await self.pending_store.get_pending_round(
            session.id, next_round_index
        )
        if pending is None:
            raise RuntimeError("Pending board not found")

        await self.pending_store.wait_for_ready(pending.generation_id, 24 * 3600)

        await self.round_scheduler.schedule_start(session)


__all__ = ["StartRoundService"]
