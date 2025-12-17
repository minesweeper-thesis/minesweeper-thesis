import logging
import uuid
from contextlib import suppress

from fastapi import BackgroundTasks

from backend.core.multi.gameplay import GameplayNotInProgress

logger = logging.getLogger(__name__)

from backend.core.game import *
from backend.di.dependencies import *
from backend.di.session_lock import SessionLockDep
from backend.lib.auth import CurrentUser
from backend.protocols.game_transport_protocol import GameTransport
from backend.repositories.exceptions import *
from backend.services.exceptions import *


class PlayMultiService:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystemDep,
        scheduler: SchedulerDep,
        game_transport_factory: GameTransportFactoryDep,
        session_lock: SessionLockDep,
    ):
        self.multi_repo = multi_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport_factory = game_transport_factory
        self.session_lock = session_lock

        self.transport: GameTransport = None  # type: ignore

    async def set_session(
        self,
        session_id: uuid.UUID,
        user: CurrentUser,
    ):
        logger.debug(f"set_session(session_id={session_id}, user_id={user.id})")
        logger.debug(f"Setting multiplayer session {session_id} for user {user.id}")
        self.session_id = session_id
        self.user = user

        self.session = await self.multi_repo.get_session(session_id)

        if self.user.id not in self.session.player_ids:
            logger.warning(f"User {user.id} is not part of session {session_id}")
            raise ValueError("User is not part of this session")

        if self.session.is_over():
            logger.warning(f"Attempted to join already finished session {session_id}")
            raise ValueError("Session is already over")

        self.transport = self.game_transport_factory.create(session_id)
        logger.info(f"User {user.id} set for multiplayer session {session_id}")

    def is_session_over(self) -> bool:
        logger.debug(f"is_session_over(session_id={self.session_id})")
        return self.session.is_over()

    async def get_game_state(self):
        logger.debug(
            f"get_game_state(session_id={self.session_id}, user_id={self.user.id})"
        )
        game_state = self.session.get_user_game_state(self.user.id)
        await self.transport.send(self.user.id, game_state)

    async def execute_action(self, action: GameAction):
        logger.debug(
            f"execute_action(session_id={self.session_id}, user_id={self.user.id}, action={type(action).__name__})"
        )
        logger.debug(
            f"User {self.user.id} executing action in session {self.session_id}: {type(action).__name__}"
        )

        async with self.session_lock.acquire(self.session_id):
            self.session = await self.multi_repo.get_session(self.session_id)

            with suppress(InvalidAction, GameplayNotInProgress):
                self.session.execute_action_for_user(self.user.id, action)

            events_by_user = self.session.consume_events()

            await self.multi_repo.save_session(self.session)

            for user_id, events in events_by_user.items():
                for event in events:
                    await self.transport.send(user_id, event)


__all__ = ["PlayMultiService"]
