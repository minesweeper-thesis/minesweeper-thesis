import uuid
from dataclasses import dataclass
from typing import Literal

from backend.core.lobby.lobby import Lobby
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


@dataclass
class InvitationAnswer:
    invitation: Invitation
    answer: Literal["accepted", "rejected"]


@dataclass
class InvitationsQuery:
    pass


__all__ = ["Invitation", "InvitationAnswer", "InvitationsQuery"]
