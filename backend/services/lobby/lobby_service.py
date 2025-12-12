import logging
import uuid

logger = logging.getLogger(__name__)

from backend.config import BACKEND_URL
from backend.core.board import DifficultyLevel, GeneratorParams
from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.repositories.exceptions import *
from backend.services.dto import KickedFromLobby
from backend.services.exceptions import *
from backend.services.lobby.helpers import *

DEV = "localhost" in BACKEND_URL


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
        difficulty_level=DifficultyLevel(10, 10, 15),
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
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.multi_repo = multi_repo
        self.notification_system = notification_system

    async def create_lobby(self, user: User) -> Lobby:
        logger.debug(f"create_lobby(user_id={user.id})")
        lobby_to_leave = self.lobby_repo.get_user_lobby(user.id)
        if lobby_to_leave:
            await self._remove_user(lobby_to_leave, user)
        lobby = Lobby(id=uuid.uuid4(), host=user, game_config=DEFAULT_GAME_CONFIG)
        self.lobby_repo.save_lobby(lobby)
        session = await create_session(lobby.id, lobby)
        await self.multi_repo.save_session(session)
        logger.info(f"Lobby {lobby.id} created by user {user.id}")
        return lobby

    async def join_lobby(self, user: User, invitation_id: uuid.UUID):
        logger.debug(f"join_lobby(user_id={user.id}, invitation_id={invitation_id})")
        lobby_to_leave = self.lobby_repo.get_user_lobby(user.id)
        if lobby_to_leave:
            await self._remove_user(lobby_to_leave, user)

        invitation = self.lobby_repo.get_invitation(invitation_id)
        lobby = invitation.lobby

        if invitation.invitee != user or invitation.lobby != lobby:
            logger.warning(
                f"User {user.id} not authorized to join lobby via invitation {invitation_id}"
            )
            raise PermissionError("User not authorized to join this lobby")

        data = lobby.add_user(user)
        self.lobby_repo.save_lobby(lobby)
        await self._sync_session_players(lobby)
        self.lobby_repo.delete_invitation(invitation.id)

        response = InvitationAnswer(invitation=invitation, answer="accepted")
        await self.notification_system.notify(invitation.inviter.id, response)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, data)

        logger.info(f"User {user.id} joined lobby {lobby.id}")
        return lobby

    async def update_lobby(
        self, lobby_id: uuid.UUID, user: User, game_config: GameConfig
    ):
        logger.debug(f"update_lobby(lobby_id={lobby_id}, user_id={user.id})")
        lobby = self.lobby_repo.get_lobby(lobby_id)

        ensure_lobby_exists(lobby)
        ensure_user_is_host(lobby, user)

        event = lobby.update_game_config(game_config)
        session = await self.multi_repo.get_pending_for_lobby(lobby.id)
        if session is not None:
            session.game_config = game_config
            await self.multi_repo.save_session(session)

        self.lobby_repo.save_lobby(lobby)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, event)

        logger.info(f"Lobby {lobby_id} config updated by user {user.id}")

    async def remove_user_from_lobby(self, lobby_id: uuid.UUID, user: User):
        logger.debug(f"remove_user_from_lobby(lobby_id={lobby_id}, user_id={user.id})")
        lobby = self.lobby_repo.get_lobby(lobby_id)

        ensure_lobby_exists(lobby)
        ensure_user_in_lobby(lobby, user)

        await self._remove_user(lobby, user)

    async def kick_from_lobby(
        self, lobby_id: uuid.UUID, user: User, target_user_id: uuid.UUID
    ):
        logger.debug(
            f"kick_from_lobby(lobby_id={lobby_id}, user_id={user.id}, target_user_id={target_user_id})"
        )
        lobby = self.lobby_repo.get_lobby(lobby_id)

        ensure_lobby_exists(lobby)
        ensure_user_is_host(lobby, user)

        target_user = await self.user_repo.get_user(target_user_id)
        if not target_user:
            raise ValueError("Target user not found")

        ensure_user_in_lobby(lobby, target_user)

        await self._remove_user(lobby, target_user)

        kicked_data = KickedFromLobby(lobby_id)
        await self.notification_system.notify(target_user.id, kicked_data)
        logger.info(f"User {target_user_id} kicked from lobby {lobby_id} by {user.id}")

    async def _remove_user(self, lobby: Lobby, user: User):
        logger.debug(f"_remove_user(lobby_id={lobby.id}, user_id={user.id})")
        data = lobby.remove_user(user)

        if lobby.is_empty():
            self.lobby_repo.delete_lobby(lobby.id)
        else:
            self.lobby_repo.save_lobby(lobby)
            await self._sync_session_players(lobby)
            for lobby_user in lobby.users:
                await self.notification_system.notify(lobby_user.id, data)

    async def _sync_session_players(self, lobby: Lobby) -> None:
        session = await self.multi_repo.get_session(lobby.id)

        if not session.is_started() and not session.is_over():
            session.set_player_ids([user.id for user in lobby.users])
            await self.multi_repo.save_session(session)


__all__ = ["LobbyService"]
