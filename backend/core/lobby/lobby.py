import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from backend.core.multi.config import GameConfig, GameConfigUpdated
from backend.core.user import User


@dataclass
class LobbyChatMessage:
    lobby_id: uuid.UUID
    sender: User
    content: str
    timestamp: datetime


@dataclass
class UserConnectionUpdated:
    lobby_id: uuid.UUID
    user: User
    status: Literal["connected", "disconnected"]


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

    def add_user(self, user: User) -> UserConnectionUpdated:
        self.users.append(user)
        return UserConnectionUpdated(lobby_id=self.id, user=user, status="connected")

    def remove_user(self, user: User) -> UserConnectionUpdated:
        if user not in self.users:
            raise ValueError("User not in lobby.")

        self.users.remove(user)

        if self.host == user:
            if self.users:
                self.host = self.users[0]
            else:
                self.host = None  # type: ignore

        return UserConnectionUpdated(lobby_id=self.id, user=user, status="disconnected")

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

    def update_game_config(self, new_config: GameConfig):
        self.game_config = new_config

        return GameConfigUpdated(lobby_id=self.id, game_config=new_config)

    def reset_ready_for_new_session(self):
        self._ready_users.clear()


__all__ = ["Lobby", "LobbyChatMessage", "UserConnectionUpdated"]
