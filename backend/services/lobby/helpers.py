from typing import Optional

from backend.core.lobby import Lobby
from backend.core.user import User


def ensure_lobby_exists(lobby: Optional[Lobby]):
    if not lobby:
        raise ValueError("Lobby not found")


def ensure_user_in_lobby(lobby: Lobby, user: User):
    if user not in lobby.users:
        raise PermissionError("User not in the lobby")


def ensure_user_is_host(lobby: Lobby, user: User):
    if lobby.host != user:
        raise PermissionError("User is not the host of the lobby")


__all__ = ["ensure_lobby_exists", "ensure_user_in_lobby", "ensure_user_is_host"]
