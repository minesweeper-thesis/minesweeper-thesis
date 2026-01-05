import uuid
from dataclasses import dataclass
from datetime import datetime

from backend.core.lobby.exceptions import SessionActive
from backend.core.multi.config import GameConfig
from backend.core.multi.session import MultiplayerSession
from backend.core.user import User


@dataclass
class LobbyChatMessage:
    lobby_id: uuid.UUID
    sender: User
    content: str
    timestamp: datetime


class UserNotInLobby(Exception):
    pass


class UserNotHost(Exception):
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

    def kick_user(self, current_user: User, target_user: User) -> None:
        self.ensure_user_is_host(current_user)
        self.ensure_user_in_lobby(target_user)

        self.remove_user(target_user)

    def is_empty(self) -> bool:
        return not len(self.users)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Lobby):
            return False
        return self.id == value.id

    def update_game_config(
        self, user: User, new_config: GameConfig, session: MultiplayerSession
    ) -> None:
        self.ensure_user_is_host(user)
        if session.is_active():
            raise SessionActive()
        self.game_config = new_config

    def ensure_user_in_lobby(self, user: User):
        if user not in self.users:
            raise UserNotInLobby()

    def ensure_user_is_host(self, user: User):
        if self.host != user:
            raise UserNotHost()


__all__ = [
    "Lobby",
    "LobbyChatMessage",
    "UserNotInLobby",
    "SessionActive",
    "UserNotHost",
]
