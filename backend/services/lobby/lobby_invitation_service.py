import uuid

from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.repositories.exceptions import *
from backend.services.exceptions import *
from backend.services.lobby.helpers import *


class LobbyInvitationService:
    def __init__(
        self,
        lobby_repo: LobbyRepositoryDep,
        user_repo: UserRepositoryDep,
        notification_system: NotificationSystemDep,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.notification_system = notification_system

    async def invite_to_lobby(
        self, lobby_id: uuid.UUID, user: User, invitee_id: uuid.UUID
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)

        ensure_lobby_exists(lobby)
        ensure_user_is_host(lobby, user)

        invitee = await self.user_repo.get_user(invitee_id)
        if not invitee:
            raise ValueError("Invitee not found")

        invitation = Invitation(
            id=uuid.uuid4(),
            lobby=lobby,
            inviter=user,
            invitee=invitee,
        )
        await self.notification_system.notify(invitation.invitee.id, invitation)
        self.lobby_repo.save_invitation(invitation)

    async def reject_game_invitation(self, invitation_id: uuid.UUID, user: User):
        invitation = self.lobby_repo.get_invitation(invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.invitee != user:
            raise PermissionError("User not authorized to reject this invitation")

        response = InvitationAnswer(invitation=invitation, answer="rejected")
        await self.notification_system.notify(invitation.inviter.id, response)
        self.lobby_repo.delete_invitation(invitation.id)

    async def get_pending_invitations(self, user: User) -> list[Invitation]:
        return self.lobby_repo.get_pending_invitations(user)


__all__ = ["LobbyInvitationService"]
