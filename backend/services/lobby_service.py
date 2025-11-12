import uuid
from typing import Annotated, Any, Awaitable, Callable

from fastapi import Depends

from backend import repositories
from backend.core.game import *
from backend.core.lobby import *
from backend.core.user import User
from backend.repositories.exceptions import *
from backend.services.exceptions import *


@dataclass
class GameConfigUpdated:
    lobby_id: uuid.UUID
    game_config: GameConfig


@dataclass
class UserConnectionUpdated(UserConnectionStatus):
    lobby_id: uuid.UUID


LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]
UserRepository = Annotated[repositories.UserRepository, Depends()]

type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


class LobbyService:
    def __init__(self, lobby_repo: LobbyRepository, user_repo: UserRepository):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo

    async def create_lobby(self, user: User) -> Lobby:
        lobby = Lobby(id=uuid.uuid4(), host=user)
        self.lobby_repo.save_lobby(lobby)
        return lobby

    async def join_lobby(
        self,
        user: User,
        invitation_id: uuid.UUID,
        notify: Notify,
    ):
        invitation = self.lobby_repo.get_invitation(invitation_id)
        lobby = invitation.lobby

        if invitation.invitee != user or invitation.lobby != lobby:
            raise PermissionError("User not authorized to join this lobby")

        lobby.add_user(user)
        self.lobby_repo.save_lobby(lobby)
        self.lobby_repo.delete_invitation(invitation.id)

        response = InvitationAnswer(invitation=invitation, answer="accepted")
        await notify(invitation.inviter.id, response)

        data = UserConnectionUpdated(user=user, status="connected", lobby_id=lobby.id)

        for lobby_user in lobby.users:
            await notify(lobby_user.id, data)

        return lobby

    async def update_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
        game_settings: GameConfig,
        notify: Notify,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        if lobby.host != user:
            raise PermissionError("User not authorized to update lobby")

        lobby.game_settings = game_settings

        self.lobby_repo.save_lobby(lobby)
        data = GameConfigUpdated(lobby.id, game_settings)
        for lobby_user in lobby.users:
            await notify(lobby_user.id, data)

    async def invite_to_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
        invitee_id: uuid.UUID,
        notify: Notify,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        if lobby.host != user:
            raise PermissionError("User not authorized to invite")

        invitee = await self.user_repo.get_user(invitee_id)
        if not invitee:
            raise ValueError("Invitee not found")

        invitation = Invitation(
            id=uuid.uuid4(),
            lobby=lobby,
            inviter=user,
            invitee=invitee,
        )
        await notify(invitation.invitee.id, invitation)
        self.lobby_repo.save_invitation(invitation)

    async def reject_game_invitation(
        self,
        invitation_id: uuid.UUID,
        user: User,
        notify: Notify,
    ):
        invitation = self.lobby_repo.get_invitation(invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.invitee != user:
            raise PermissionError("User not authorized to reject this invitation")

        response = InvitationAnswer(invitation=invitation, answer="rejected")
        await notify(invitation.inviter.id, response)
        self.lobby_repo.delete_invitation(invitation.id)

    async def remove_user_from_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
        notify: Notify,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        lobby.remove_user(user)

        if lobby.is_empty():
            self.lobby_repo.delete_lobby(lobby_id)
        else:
            self.lobby_repo.save_lobby(lobby)
            data = UserConnectionUpdated(
                user=user, status="disconnected", lobby_id=lobby.id
            )
            for lobby_user in lobby.users:
                await notify(lobby_user.id, data)
