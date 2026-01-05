import uuid
from dataclasses import dataclass
from typing import Literal, Optional

from backend.core.lobby import Lobby
from backend.core.multi import GameConfig
from backend.core.user import User


@dataclass
class KickedFromLobby:
    lobby_id: uuid.UUID


@dataclass
class NewHostAssigned:
    lobby_id: uuid.UUID
    host: User


@dataclass
class UserCurrentLobby:
    lobby: Optional[Lobby]


@dataclass
class UserConnectionUpdated:
    lobby_id: uuid.UUID
    user: User
    status: Literal["connected", "disconnected"]


@dataclass
class UserOnlineUpdated:
    lobby_id: uuid.UUID
    user: User


@dataclass
class GameConfigUpdated:
    lobby_id: uuid.UUID
    game_config: GameConfig


__all__ = [
    "KickedFromLobby",
    "UserCurrentLobby",
    "UserOnlineUpdated",
    "UserConnectionUpdated",
    "GameConfigUpdated",
    "NewHostAssigned",
]
