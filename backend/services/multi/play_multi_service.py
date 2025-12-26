import logging
import uuid
from contextlib import suppress
from typing import Annotated

from fastapi import BackgroundTasks, Depends

from backend.core.multi.gameplay import GameplayNotInProgress
from backend.core.user import User
from backend.services.exceptions import SessionNotExists, UserNotInSession

logger = logging.getLogger(__name__)

from backend.core.game import *
from backend.di.dependencies import *
from backend.di.session_lock import SessionLockDep
from backend.protocols.game_transport_protocol import GameTransport
from backend.services.exceptions import *
from backend.services.multi.session_renewer import SessionRenewer


class PlayMultiService:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        background_tasks: BackgroundTasks,
        scheduler: SchedulerDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
        session_lock: SessionLockDep,
        session_renewer: Annotated[SessionRenewer, Depends()],
    ):
        self.multi_repo = multi_repo
        self.background_tasks = background_tasks
        self.scheduler = scheduler
        self.lobby_transport_factory = lobby_transport_factory
        self.session_lock = session_lock
        self.session_renewer = session_renewer

        self.transport: GameTransport = None  # type: ignore

    async def validate_session(
        self,
        lobby_id: uuid.UUID,
        user: User,
    ):
        logger.debug(f"validate_session(lobby_id={lobby_id}, user_id={user.id})")

        session = await self.multi_repo.get_for_lobby(lobby_id)

        if session is None:
            logger.warning(f"No active session for lobby {lobby_id}")
            raise SessionNotExists()

        self.session_id = session.id
        self.user = user

        await self.reload(user)

        if self.user.id not in self.session.player_ids:
            logger.warning(f"User {user.id} is not part of session {self.session_id}")
            raise UserNotInSession()

        if self.session.is_over():
            logger.warning(
                f"Attempted to join already finished session {self.session_id}"
            )
            raise SessionAlreadyOver()

        self.transport = self.lobby_transport_factory.create(session.lobby_id)
        logger.info(f"User {user.id} set for multiplayer session {self.session_id}")

    async def reload(self, user: User):
        logger.debug(
            f"load_session(session_id={self.session_id}, user_id={self.user.id})"
        )
        self.session = await self.multi_repo.get_session(self.session_id)
        self.user = user

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

            if self.session.is_over():
                await self.session_renewer.renew_session(self.session.lobby_id)


__all__ = ["PlayMultiService"]
