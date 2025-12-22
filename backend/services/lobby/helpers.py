from backend.core.lobby import Lobby
from backend.core.lobby.lobby import UserNotInLobby
from backend.core.user import User
from backend.services.exceptions import UserNotHost


def ensure_user_in_lobby(lobby: Lobby, user: User):
    if user not in lobby.users:
        raise UserNotInLobby()


def ensure_user_is_host(lobby: Lobby, user: User):
    if lobby.host != user:
        raise UserNotHost()


__all__ = ["ensure_user_in_lobby", "ensure_user_is_host"]
