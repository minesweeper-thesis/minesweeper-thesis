import uuid
from dataclasses import dataclass
from typing import Literal, Optional

from backend.core.board import DifficultyLevel, GeneratorSettings, GeneratorType
from backend.core.game import GameMode
from backend.core.user import User


@dataclass
class GameConfig:
    rounds: int
    max_round_time: int
    difficulty_level: DifficultyLevel
    game_mode: GameMode
    generator_type: GeneratorType
    generator_settings: Optional[GeneratorSettings] = None


class Lobby:
    id: uuid.UUID
    host: User
    users: list[User]
    game_config: GameConfig

    def __init__(self, id: uuid.UUID, host: User, game_config: GameConfig):
        self.id = id
        self.host = host
        self.users = [host]
        self.game_config = game_config
        self._ready_users: set[uuid.UUID] = set()

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

    def set_user_ready(self, user: User) -> None:
        self._ready_users.add(user.id)

    def is_user_ready(self, user: User) -> bool:
        return user.id in self._ready_users

    def set_user_not_ready(self, user: User) -> None:
        self._ready_users.discard(user.id)

    def all_users_ready(self) -> bool:
        return all(user.id in self._ready_users for user in self.users)


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
