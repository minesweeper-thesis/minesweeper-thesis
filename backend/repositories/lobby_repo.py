import uuid
from collections import defaultdict
from contextlib import suppress

from fastapi_pagination import Params

from backend.core.lobby import ChatMessage, Invitation, Lobby

lobbies: dict[uuid.UUID, Lobby] = {}
invitations: dict[uuid.UUID, Invitation] = {}

messages: dict[uuid.UUID, list[ChatMessage]] = defaultdict(list)


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

    def get_user_lobbies(self, user) -> list[Lobby]:
        return [lobby for lobby in lobbies.values() if user in lobby.users]

    def add_message(self, message: ChatMessage) -> None:
        messages[message.lobby_id].append(message)

    def get_messages(
        self, lobby_id: uuid.UUID, pagination_params: Params
    ) -> list[ChatMessage]:
        all_messages = messages[lobby_id]
        start = (pagination_params.page - 1) * pagination_params.size
        end = start + pagination_params.size
        return sorted(all_messages, key=lambda msg: msg.timestamp, reverse=True)[
            start:end
        ]
