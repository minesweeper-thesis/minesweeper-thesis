import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.lobby import Lobby
from backend.core.user import User


@dataclass
class KickedFromLobby:
    lobby_id: uuid.UUID


@dataclass
class UserCurrentLobby:
    lobby: Optional[Lobby]


@dataclass
class UserOnlineUpdated:
    lobby_id: uuid.UUID
    user: User


__all__ = ["KickedFromLobby", "UserCurrentLobby", "UserOnlineUpdated"]
