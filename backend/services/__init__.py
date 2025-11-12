from .friends_service import FriendsService
from .lobby_service import LobbyService
from .multiplayer_service import MultiplayerService
from .singleplayer_service import SingleplayerService
from .stats_service import StatsService
from .user_service import UserService

__all__ = [
    "UserService",
    "FriendsService",
    "SingleplayerService",
    "MultiplayerService",
    "StatsService",
    "LobbyService",
]
