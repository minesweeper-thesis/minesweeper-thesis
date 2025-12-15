from typing import Callable

from fastapi import Depends

from backend import protocols as p
from backend.config import REDIS_URL
from backend.lib.board_generator import LocalBoardGenerator
from backend.lib.pending_boards import get_pending_boards_store
from backend.lib.scheduler import get_scheduler
from backend.repositories import *


def _get_notification_system():
    from backend.lib.notification_system import get_notification_system

    return get_notification_system()


def _get_game_transport_factory():
    from backend.lib.session_game_transport import get_game_transport_factory

    return get_game_transport_factory()


_lobby_repo = InMemoryLobbyRepository()


def _get_lobby_repo():
    return _lobby_repo if REDIS_URL is None else RedisLobbyRepository()


registry: dict[type, Callable] = {
    p.BoardRepository: BoardRepository,
    p.SingleplayerRepository: SingleplayerRepository,
    p.MultiplayerRepository: (
        RedisMultiplayerRepository if REDIS_URL else InMemoryMultiplayerRepository
    ),
    p.UserRepository: UserRepository,
    p.FriendsRepository: FriendsRepository,
    p.StatsRepository: StatsRepository,
    p.LobbyRepository: _get_lobby_repo,
    p.BoardGenerator: LocalBoardGenerator,
    p.PendingBoardsStore: get_pending_boards_store,
    p.NotificationSystem: _get_notification_system,
    p.GameTransportFactory: _get_game_transport_factory,
    p.Scheduler: get_scheduler,
}

for protocol, impl in registry.items():
    registry[protocol] = Depends(impl)
