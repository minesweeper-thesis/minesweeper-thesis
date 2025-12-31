import logging
import uuid

from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.protocols.lobby_repo_protocol import LobbyNotFound
from backend.protocols.user_repo_protocol import UserNotFound
from backend.services.exceptions import *
from backend.services.lobby.helpers import *

logger = logging.getLogger(__name__)


class LobbyInvitationService:
    def __init__(
        self,
        lobby_repo: LobbyRepositoryDep,
        user_repo: UserRepositoryDep,
        notification_system: NotificationSystemDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.notification_system = notification_system
        self.lobby_transport_factory = lobby_transport_factory

    async def lobby_notify(self, lobby: Lobby, receiver_id: uuid.UUID, data):
        transport = self.lobby_transport_factory.get(lobby.id)
        await transport.send(receiver_id, data)

    async def invite_to_lobby(
        self, lobby_id: uuid.UUID, user: User, invitee_id: uuid.UUID
    ):
        try:
            logger.debug(
                f"invite_to_lobby(lobby_id={lobby_id}, user_id={user.id}, invitee_id={invitee_id})"
            )
            lobby = await self.lobby_repo.get_lobby(lobby_id)

            ensure_user_is_host(lobby, user)

            invitee = await self.user_repo.get_user(invitee_id)
            invitation = Invitation(
                id=uuid.uuid4(),
                lobby=lobby,
                inviter=user,
                invitee=invitee,
            )
            await self.notification_system.notify(invitation.invitee.id, invitation)
            await self.lobby_repo.save_invitation(invitation, timedelta(hours=1))
            logger.info(f"User {user.id} invited user {invitee_id} to lobby {lobby_id}")

        except UserNotFound:
            raise UserNotExists() from None
        except LobbyNotFound:
            raise LobbyNotExists() from None

    async def reject_game_invitation(self, invitation_id: uuid.UUID, user: User):
        logger.debug(
            f"reject_game_invitation(invitation_id={invitation_id}, user_id={user.id})"
        )
        invitation = await self.lobby_repo.get_invitation(invitation_id)
        if not invitation or invitation.invitee != user:
            raise InvitationNotExists()

        response = InvitationAnswer(invitation=invitation, answer="rejected")
        await self.lobby_notify(invitation.lobby, invitation.inviter.id, response)
        await self.lobby_repo.delete_invitation(invitation.id)
        logger.info(f"User {user.id} rejected invitation {invitation_id}")

    async def get_pending_invitations(self, user: User) -> list[Invitation]:
        logger.debug(f"get_pending_invitations(user_id={user.id})")
        return await self.lobby_repo.get_pending_invitations(user.id)


__all__ = ["LobbyInvitationService"]
