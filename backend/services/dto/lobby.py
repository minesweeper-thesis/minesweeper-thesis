import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from backend.core.lobby import Lobby
from backend.core.multi import GameConfig, SessionScoreboard
from backend.core.user import User


@dataclass
class KickedFromLobby:
    lobby_id: uuid.UUID


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


@dataclass
class SessionStateRoundData:
    round_number: int
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    countdown_to: Optional[datetime]
    state: Literal["not_ready", "generating", "countdown", "ready_lock", "playing"]


@dataclass
class SessionState:
    session_id: uuid.UUID
    round: SessionStateRoundData
    scoreboard: SessionScoreboard


__all__ = [
    "KickedFromLobby",
    "UserCurrentLobby",
    "UserOnlineUpdated",
    "SessionState",
    "SessionStateRoundData",
    "UserConnectionUpdated",
    "GameConfigUpdated",
]
