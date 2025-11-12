import uuid
from dataclasses import dataclass
from typing import Literal, Optional

from backend.core.board import DifficultyLevel, GeneratorSettings, GeneratorType
from backend.core.game import GameMode
from backend.core.user import User


@dataclass
class GameConfig:
    difficulty_level: DifficultyLevel
    game_mode: GameMode
    generator_type: GeneratorType
    generator_settings: Optional[GeneratorSettings] = None


DEFAULT_GAME_CONFIG = GameConfig(
    difficulty_level=DifficultyLevel(10, 10, 15),
    game_mode="normal",
    generator_type="random",
    generator_settings=None,
)


class Lobby:
    id: uuid.UUID
    host: User
    users: list[User]
    game_settings: GameConfig

    def __init__(self, id: uuid.UUID, host: User):
        self.id = id
        self.host = host
        self.users = [host]
        self.game_settings = DEFAULT_GAME_CONFIG

    def add_user(self, user: User) -> None:
        self.users.append(user)

    def remove_user(self, user: User) -> None:
        if user not in self.users:
            raise ValueError("User not in lobby.")

        self.users.remove(user)

        if self.host == user:
            if self.users:
                self.host = self.users[0]
            else:
                self.host = None  # type: ignore

    def is_empty(self) -> bool:
        return not len(self.users)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Lobby):
            return False
        return self.id == value.id


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
class UserConnectionStatus:
    user: User
    status: Literal["connected", "disconnected"]
