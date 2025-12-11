import logging
import uuid
from collections import defaultdict
from contextlib import suppress
from typing import Optional

from fastapi_pagination import Page, Params

logger = logging.getLogger(__name__)

from backend import protocols
from backend.core.lobby import Invitation, Lobby, LobbyChatMessage

lobbies: dict[uuid.UUID, Lobby] = {}
invitations: dict[uuid.UUID, Invitation] = {}

messages: dict[uuid.UUID, list[LobbyChatMessage]] = defaultdict(list)


class LobbyNotFound(Exception):
    pass


class InvitationNotFound(Exception):
    pass


class LobbyRepository(protocols.LobbyRepository):
    def __init__(self):
        pass

    def save_lobby(self, lobby: Lobby):
        logger.debug(f"save_lobby(lobby_id={lobby.id}, users={len(lobby.users)})")
        lobbies[lobby.id] = lobby
        logger.debug(f"Lobby {lobby.id} saved with {len(lobby.users)} users")

    def get_lobby(self, lobby_id: uuid.UUID) -> Lobby:
        logger.debug(f"get_lobby(lobby_id={lobby_id})")
        try:
            return lobbies[lobby_id]

        except KeyError:
            raise LobbyNotFound(f"Lobby with id {lobby_id} not found.") from None

    def delete_lobby(self, lobby_id: uuid.UUID) -> None:
        logger.debug(f"delete_lobby(lobby_id={lobby_id})")
        with suppress(KeyError):
            del lobbies[lobby_id]
            logger.info(f"Lobby {lobby_id} deleted")

    def save_invitation(self, invitation: Invitation):
        logger.debug(
            f"save_invitation(invitation_id={invitation.id}, inviter={invitation.inviter.id}, invitee={invitation.invitee.id})"
        )
        invitations[invitation.id] = invitation
        logger.info(
            f"Invitation {invitation.id} saved from {invitation.inviter.nickname} to {invitation.invitee.nickname}"
        )

    def get_invitation(self, invitation_id: uuid.UUID) -> Invitation:
        logger.debug(f"get_invitation(invitation_id={invitation_id})")
        try:
            return invitations[invitation_id]

        except KeyError:
            raise InvitationNotFound(
                f"Invitation with id {invitation_id} not found."
            ) from None

    def delete_invitation(self, invitation_id: uuid.UUID) -> None:
        logger.debug(f"delete_invitation(invitation_id={invitation_id})")
        with suppress(KeyError):
            del invitations[invitation_id]
            logger.debug(f"Invitation {invitation_id} deleted")

    def get_pending_invitations(self, user_id: uuid.UUID) -> list[Invitation]:
        logger.debug(f"get_pending_invitations(user_id={user_id})")
        return [
            invitation
            for invitation in invitations.values()
            if invitation.invitee.id == user_id
        ]

    def get_user_lobby(self, user_id: uuid.UUID) -> Optional[Lobby]:
        logger.debug(f"get_user_lobby(user_id={user_id})")
        for lobby in lobbies.values():
            if any(user.id == user_id for user in lobby.users):
                return lobby
        return None

    def add_message(self, message: LobbyChatMessage) -> None:
        logger.debug(
            f"add_message(lobby_id={message.lobby_id}, sender={message.sender.id})"
        )
        messages[message.lobby_id].append(message)

    def get_messages(self, lobby_id: uuid.UUID, pagination_params: Params):
        logger.debug(
            f"get_messages(lobby_id={lobby_id}, page={pagination_params.page})"
        )
        all_messages = messages[lobby_id]
        start = (pagination_params.page - 1) * pagination_params.size
        end = start + pagination_params.size
        items = sorted(all_messages, key=lambda msg: msg.timestamp, reverse=True)[
            start:end
        ]
        return Page.create(
            items=items, total=len(all_messages), params=pagination_params
        )
