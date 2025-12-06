import uuid
from typing import Annotated

from fastapi import Depends

from backend import repositories
from backend.core.board import DifficultyLevel
from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.repositories.exceptions import *
from backend.services.dto import KickedFromLobby
from backend.services.exceptions import *
from backend.services.lobby.helpers import *

LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]
UserRepository = Annotated[repositories.UserRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]

DEFAULT_GAME_CONFIG = GameConfig(
    rounds=3,
    max_round_time=60,
    difficulty_level=DifficultyLevel(3, 3, 3),
    game_mode="normal",
    generator=Generator(generator_type="random"),
)


class LobbyService:
    def __init__(
        self,
        lobby_repo: LobbyRepository,
        user_repo: UserRepository,
        notification_system: NotificationSystem,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.notification_system = notification_system

    async def create_lobby(self, user: User) -> Lobby:
        lobby = Lobby(id=uuid.uuid4(), host=user, game_config=DEFAULT_GAME_CONFIG)
        self.lobby_repo.save_lobby(lobby)
        return lobby

    async def get_user_lobby(self, user: User) -> Optional[Lobby]:
        if lobbies := self.lobby_repo.get_user_lobbies(user):
            return lobbies[0]
        return None

    async def join_lobby(self, user: User, invitation_id: uuid.UUID):
        user_lobby = self.lobby_repo.get_user_lobbies(user)
        if user_lobby:
            lobby_to_leave = user_lobby[0]
            await self._remove_user(lobby_to_leave, user)

        invitation = self.lobby_repo.get_invitation(invitation_id)
        lobby = invitation.lobby

        if invitation.invitee != user or invitation.lobby != lobby:
            raise PermissionError("User not authorized to join this lobby")

        data = lobby.add_user(user)
        self.lobby_repo.save_lobby(lobby)
        self.lobby_repo.delete_invitation(invitation.id)

        response = InvitationAnswer(invitation=invitation, answer="accepted")
        await self.notification_system.notify(invitation.inviter.id, response)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, data)

        return lobby

    async def update_lobby(
        self, lobby_id: uuid.UUID, user: User, game_config: GameConfig
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)

        ensure_lobby_exists(lobby)
        ensure_user_is_host(lobby, user)

        event = lobby.update_game_config(game_config)

        self.lobby_repo.save_lobby(lobby)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, event)

    async def remove_user_from_lobby(self, lobby_id: uuid.UUID, user: User):
        lobby = self.lobby_repo.get_lobby(lobby_id)

        ensure_lobby_exists(lobby)
        ensure_user_in_lobby(lobby, user)

        await self._remove_user(lobby, user)

    async def kick_from_lobby(
        self, lobby_id: uuid.UUID, user: User, target_user_id: uuid.UUID
    ):
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

    async def _remove_user(self, lobby: Lobby, user: User):
        data = lobby.remove_user(user)

        if lobby.is_empty():
            self.lobby_repo.delete_lobby(lobby.id)
        else:
            self.lobby_repo.save_lobby(lobby)
            for lobby_user in lobby.users:
                await self.notification_system.notify(lobby_user.id, data)


__all__ = ["LobbyService"]
