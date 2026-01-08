import logging
import uuid
from datetime import timedelta

from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.protocols.repos.exceptions import (
    InvitationNotFound,
    LobbyNotFound,
    SessionNotFound,
    UserNotFound,
)
from backend.services.exceptions import *

logger = logging.getLogger(__name__)


class LobbyInvitationService:
    def __init__(
        self,
        user_repo: UserRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        lobby_repo: LobbyRepositoryDep,
        notification_system: NotificationSystemDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
    ):
        self.user_repo = user_repo
        self.multi_repo = multi_repo
        self.lobby_repo = lobby_repo
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

            lobby.ensure_user_is_host(user)

            invitee = await self.user_repo.get_user(invitee_id)
            invitation = Invitation(
                id=uuid.uuid4(),
                lobby=lobby,
                inviter=user,
                invitee=invitee,
            )
            await self.notification_system.notify(invitation.invitee.id, invitation)
            await self.lobby_repo.save_invitation(invitation, timedelta(minutes=10))
            logger.info(f"User {user.id} invited user {invitee_id} to lobby {lobby_id}")

        except UserNotFound:
            raise UserNotExists() from None
        except LobbyNotFound:
            raise LobbyNotExists() from None

    async def reject_game_invitation(self, invitation_id: uuid.UUID, user: User):
        logger.debug(
            f"reject_game_invitation(invitation_id={invitation_id}, user_id={user.id})"
        )
        try:
            invitation = await self.lobby_repo.get_invitation(invitation_id)
            lobby = await self.lobby_repo.get_lobby(invitation.lobby.id)
            session = await self.multi_repo.get_for_lobby(lobby.id)

            invitation.validate(user, lobby, session)

            response = InvitationAnswer(invitation=invitation, answer="rejected")
            await self.lobby_notify(invitation.lobby, invitation.inviter.id, response)
            await self.lobby_repo.delete_invitation(invitation.id)
            logger.info(f"User {user.id} rejected invitation {invitation_id}")
        except (InvitationNotFound, LobbyNotFound, SessionNotFound):
            raise InvitationNotExists() from None

    async def get_pending_invitations(self, user: User) -> list[Invitation]:
        logger.debug(f"get_pending_invitations(user_id={user.id})")
        return await self.lobby_repo.get_pending_invitations(user.id)


__all__ = ["LobbyInvitationService"]
