import logging
import uuid
from typing import Annotated

from fastapi import Depends

from backend.config import DEV
from backend.core.board import DifficultyLevel, GeneratorParams
from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.protocols.repos.exceptions import (
    InvitationNotFound,
    LobbyNotFound,
    SessionNotFound,
)
from backend.protocols.repos.user_repo_protocol import UserNotFound
from backend.services.dto import (
    GameConfigUpdated,
    KickedFromLobby,
    UserConnectionUpdated,
)
from backend.services.exceptions import *
from backend.services.exceptions import UserNotExists
from backend.services.multi.session_renewer import SessionRenewer

logger = logging.getLogger(__name__)


DEFAULT_GAME_CONFIG = (
    GameConfig(
        rounds=3,
        max_round_time=60,
        difficulty_level=DifficultyLevel(3, 3, 3),
        game_mode="normal",
        generator=Generator(generator_type="random"),
    )
    if DEV
    else GameConfig(
        rounds=3,
        max_round_time=60,
        difficulty_level=DifficultyLevel.easy(),
        game_mode="normal",
        generator=Generator(
            generator_type="ml",
            settings=GeneratorParams(classifier="lightgbm"),
        ),
    )
)


class LobbyService:
    def __init__(
        self,
        lobby_repo: LobbyRepositoryDep,
        user_repo: UserRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        notification_system: NotificationSystemDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
        session_lock: SessionLockDep,
        session_renewer: Annotated[SessionRenewer, Depends()],
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.multi_repo = multi_repo
        self.notification_system = notification_system
        self.lobby_transport_factory = lobby_transport_factory
        self.session_lock = session_lock
        self.session_renewer = session_renewer

    async def create_lobby(self, user: User) -> Lobby:
        logger.debug(f"create_lobby(user_id={user.id})")
        lobby_to_leave = await self.lobby_repo.get_user_lobby(user.id)
        if lobby_to_leave:
            lobby_to_leave.remove_user(user)
            await self._on_remove(lobby_to_leave, user)

        lobby = Lobby(id=uuid.uuid4(), host=user, game_config=DEFAULT_GAME_CONFIG)
        await self.lobby_repo.save_lobby(lobby)

        session = await create_session(lobby)
        await self.multi_repo.save_session(session)
        logger.debug(
            f"Created session {session.id} for lobby {lobby.id}, game_config={session.game_config}"
        )

        logger.info(f"Lobby {lobby.id} created by user {user.id}")

        return lobby

    async def join_lobby(self, user: User, invitation_id: uuid.UUID):
        logger.debug(f"join_lobby(user_id={user.id}, invitation_id={invitation_id})")
        lobby_to_leave = await self.lobby_repo.get_user_lobby(user.id)
        if lobby_to_leave:
            lobby_to_leave.remove_user(user)
            await self._on_remove(lobby_to_leave, user)

        try:
            invitation = await self.lobby_repo.get_invitation(invitation_id)
            lobby = await self.lobby_repo.get_lobby(invitation.lobby.id)
            session = await self.multi_repo.get_for_lobby(lobby.id)

            try:
                invitation.validate(user, lobby, session)
            except NotAuthorizedToJoinLobby:
                logger.warning(
                    f"User {user.id} not authorized to join lobby {lobby.id} with invitation {invitation.id}"
                )
                raise
            except SessionActive:
                logger.warning(
                    f"User {user.id} attempted to join active session for lobby {lobby.id}"
                )
                raise

        except (InvitationNotFound, LobbyNotFound, SessionNotFound):
            logger.warning(
                f"Invitation {invitation_id} not found for user {user.id} when joining lobby",
                exc_info=True,
            )
            raise InvitationNotExists() from None

        lobby.add_user(user)
        await self.lobby_repo.save_lobby(lobby)
        await self.session_renewer.renew_session(lobby.id)
        await self.lobby_repo.delete_invitation(invitation.id)

        response = InvitationAnswer(invitation=invitation, answer="accepted")

        transport = self.lobby_transport_factory.get(lobby.id)
        await transport.send(invitation.inviter.id, response)
        await transport.broadcast(
            UserConnectionUpdated(lobby_id=lobby.id, user=user, status="connected")
        )

        logger.info(f"User {user.id} joined lobby {lobby.id}")
        return lobby

    async def update_lobby(
        self, lobby_id: uuid.UUID, user: User, game_config: GameConfig
    ):
        try:
            logger.debug(f"update_lobby(lobby_id={lobby_id}, user_id={user.id})")
            lobby = await self.lobby_repo.get_lobby(lobby_id)
            session = await self.multi_repo.get_for_lobby(lobby.id)

            lobby.update_game_config(user, game_config, session)
            await self.lobby_repo.save_lobby(lobby)

            await self.session_renewer.renew_session(lobby_id)

            transport = self.lobby_transport_factory.get(lobby.id)
            await transport.broadcast(
                GameConfigUpdated(lobby_id=lobby.id, game_config=game_config)
            )

            logger.info(f"Lobby {lobby_id} config updated by user {user.id}")
        except LobbyNotFound:
            raise LobbyNotExists() from None

        except SessionNotFound:
            await self.session_renewer.renew_session(lobby_id)
            transport = self.lobby_transport_factory.get(lobby.id)
            await transport.broadcast(
                GameConfigUpdated(lobby_id=lobby.id, game_config=game_config)
            )
            logger.warning(
                f"No active session found for lobby {lobby_id} during update by user {user.id}"
            )

    async def remove_user_from_lobby(self, lobby_id: uuid.UUID, user: User):
        try:
            logger.debug(
                f"remove_user_from_lobby(lobby_id={lobby_id}, user_id={user.id})"
            )
            lobby = await self.lobby_repo.get_lobby(lobby_id)

            lobby.ensure_user_in_lobby(user)

            lobby.remove_user(user)
            await self._on_remove(lobby, user)
        except LobbyNotFound:
            raise LobbyNotExists() from None

    async def kick_from_lobby(
        self, lobby_id: uuid.UUID, user: User, target_user_id: uuid.UUID
    ):
        try:
            logger.debug(
                f"kick_from_lobby(lobby_id={lobby_id}, user_id={user.id}, target_user_id={target_user_id})"
            )
            target_user = await self.user_repo.get_user(target_user_id)
            lobby = await self.lobby_repo.get_lobby(lobby_id)

            lobby.kick_user(user, target_user)
            await self._on_remove(lobby, target_user)

            kicked_data = KickedFromLobby(lobby_id)
            await self.notification_system.notify(target_user.id, kicked_data)
            logger.info(
                f"User {target_user_id} kicked from lobby {lobby_id} by {user.id}"
            )
        except LobbyNotFound:
            raise LobbyNotExists() from None
        except UserNotFound:
            raise UserNotExists() from None

    async def _on_remove(self, lobby: Lobby, user: User):
        logger.debug(f"_on_remove(lobby_id={lobby.id}, user_id={user.id})")

        if lobby.is_empty():
            await self.lobby_repo.delete_lobby(lobby.id)
        else:
            await self.lobby_repo.save_lobby(lobby)
            session = await self.multi_repo.get_for_lobby(lobby.id)

            async with self.session_lock.acquire(session.id):
                session.remove_player(user)
                await self.multi_repo.save_session(session)

            transport = self.lobby_transport_factory.get(lobby.id)
            await transport.broadcast(
                UserConnectionUpdated(
                    lobby_id=lobby.id, user=user, status="disconnected"
                )
            )


__all__ = ["LobbyService"]
