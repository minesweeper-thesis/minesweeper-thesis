import logging
import uuid
from contextlib import suppress
from typing import Annotated

from fastapi import Depends

from backend.core.game import *
from backend.core.multi.multi_gameplay import GameplayNotInProgress
from backend.core.multi.round import InvalidRoundState
from backend.core.multi.session import SessionAlreadyOver
from backend.core.user import User
from backend.di.dependencies import *
from backend.protocols.repos.exceptions import SessionNotFound
from backend.services.dto import RoundEnd, SessionOver
from backend.services.exceptions import *
from backend.services.exceptions import SessionNotExists
from backend.services.multi.session_renewer import SessionRenewer

logger = logging.getLogger(__name__)


class PlayMultiService:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        scheduler: SchedulerDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
        session_lock: SessionLockDep,
        session_renewer: Annotated[SessionRenewer, Depends()],
    ):
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.lobby_transport_factory = lobby_transport_factory
        self.session_lock = session_lock
        self.session_renewer = session_renewer

    async def load_session(self, user: User, lobby_id: uuid.UUID):
        logger.debug(f"load_session(lobby_id={lobby_id}, user_id={user.id})")
        try:
            session = await self.multi_repo.get_for_lobby(lobby_id)

            session.ensure_user_in_session(user)

            if session.is_over():
                logger.warning(
                    f"Attempted to join already finished session {session.id}"
                )
                raise SessionAlreadyOver()

            self.session = session
            self.user = user
            logger.info(f"User {user.id} set for multiplayer session {session.id}")
        except SessionNotFound:
            logger.warning(f"No active session for lobby {lobby_id}")
            raise SessionNotExists() from None

    async def get_game_state(self):
        logger.debug(f"get_game_state(user_id={self.user.id})")
        game_state = self.session.get_user_game_state(self.user)
        transport = self.lobby_transport_factory.get(self.session.lobby_id)
        await transport.send(self.user.id, game_state)

    async def execute_action(self, action: GameAction):
        logger.debug(
            f"execute_action(user_id={self.user.id}, action={type(action).__name__})"
        )

        async with self.session_lock.acquire(self.session.id):
            self.session = await self.multi_repo.get_session(self.session.id)
            if self.session._current_round.state != "playing":
                return

            with suppress(InvalidAction, GameplayNotInProgress, InvalidRoundState):
                self.session.execute_action_for_user(self.user, action)

            events_by_user = self.session.consume_events()

            await self.multi_repo.save_session(self.session)

            transport = self.lobby_transport_factory.get(self.session.lobby_id)
            await transport.send_many(events_by_user)

            if self.session._current_round.state == "ended":
                await transport.broadcast(
                    RoundEnd(
                        session_id=self.session.id,
                        round_index=self.session.current_round_index,
                        scoreboard=self.session._current_round.scoreboard,
                    )
                )

            if self.session.is_over():
                await self.session_renewer.renew_session(self.session.lobby_id)
                await transport.broadcast(
                    SessionOver(
                        session_id=self.session.id, scoreboard=self.session.scoreboard
                    )
                )


__all__ = ["PlayMultiService"]
