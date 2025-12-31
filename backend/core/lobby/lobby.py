import uuid
from dataclasses import dataclass
from datetime import datetime

from backend.core.multi.config import GameConfig
from backend.core.user import User


@dataclass
class LobbyChatMessage:
    lobby_id: uuid.UUID
    sender: User
    content: str
    timestamp: datetime


class UserNotInLobby(Exception):
    pass


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
            raise UserNotInLobby()

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

    def update_game_config(self, new_config: GameConfig) -> None:
        self.game_config = new_config

    def reset_ready_for_new_session(self):
        self._ready_users.clear()


__all__ = ["Lobby", "LobbyChatMessage"]
