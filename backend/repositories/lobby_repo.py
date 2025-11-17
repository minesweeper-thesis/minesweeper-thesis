import uuid
from contextlib import suppress

from backend.core.lobby import Invitation, Lobby

lobbies: dict[uuid.UUID, Lobby] = {}
invitations: dict[uuid.UUID, Invitation] = {}


class LobbyNotFound(Exception):
    pass


class InvitationNotFound(Exception):
    pass


class LobbyRepository:
    def save_lobby(self, lobby: Lobby):
        lobbies[lobby.id] = lobby

    def get_lobby(self, lobby_id: uuid.UUID) -> Lobby:
        try:
            return lobbies[lobby_id]

        except KeyError:
            raise LobbyNotFound(f"Lobby with id {lobby_id} not found.") from None

    def delete_lobby(self, lobby_id: uuid.UUID) -> None:
        with suppress(KeyError):
            del lobbies[lobby_id]

    def save_invitation(self, invitation: Invitation):
        invitations[invitation.id] = invitation

    def get_invitation(self, invitation_id: uuid.UUID) -> Invitation:
        try:
            return invitations[invitation_id]

        except KeyError:
            raise InvitationNotFound(
                f"Invitation with id {invitation_id} not found."
            ) from None

    def delete_invitation(self, invitation_id: uuid.UUID) -> None:
        with suppress(KeyError):
            del invitations[invitation_id]

    def get_pending_invitations(self, user) -> list[Invitation]:
        return [
            invitation
            for invitation in invitations.values()
            if invitation.invitee == user
        ]
