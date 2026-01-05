import uuid
from dataclasses import dataclass
from typing import Literal

from backend.core.lobby.exceptions import NotAuthorizedToJoinLobby, SessionActive
from backend.core.lobby.lobby import Lobby
from backend.core.multi.session import MultiplayerSession
from backend.core.user import User


class Invitation:
    id: uuid.UUID
    lobby: Lobby
    inviter: User
    invitee: User

    def __init__(self, id: uuid.UUID, lobby: Lobby, inviter: User, invitee: User):
        self.id = id
        self.lobby = lobby
        self.inviter = inviter
        self.invitee = invitee

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Invitation):
            return False
        return self.id == value.id

    def validate(self, user: User, lobby: Lobby, session: MultiplayerSession) -> None:
        if self.invitee.id != user.id or lobby.id != self.lobby.id:
            raise NotAuthorizedToJoinLobby()

        if session.is_active():
            raise SessionActive()


@dataclass
class InvitationAnswer:
    invitation: Invitation
    answer: Literal["accepted", "rejected"]


__all__ = ["Invitation", "InvitationAnswer", "NotAuthorizedToJoinLobby"]
