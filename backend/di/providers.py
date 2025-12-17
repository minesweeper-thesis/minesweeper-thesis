from typing import Callable

from fastapi import Depends

from backend import protocols as p
from backend.db.db import get_async_session
from backend.lib.board_generator import LocalBoardGenerator
from backend.lib.board_persister import BackgroundBoardPersister
from backend.lib.pending_boards import RedisPendingStore
from backend.lib.redis_client import get_redis
from backend.lib.scheduler import get_scheduler
from backend.repositories import *


def _get_notification_system():
    from backend.lib.notification_system import get_notification_system

    return get_notification_system()


def _get_game_transport_factory():
    from backend.lib.session_game_transport import get_game_transport_factory

    return get_game_transport_factory()


def _get_lobby_repository(redis=Depends(get_redis)):
    return RedisLobbyRepository(redis)


def _get_multiplayer_repository(
    session=Depends(get_async_session), redis=Depends(get_redis)
):
    return RedisMultiplayerRepository(session, redis)


def _get_pending_boards_store(redis=Depends(get_redis)):
    return RedisPendingStore(redis)


registry: dict[type, Callable] = {
    p.BoardRepository: BoardRepository,
    p.SingleplayerRepository: SingleplayerRepository,
    p.MultiplayerRepository: _get_multiplayer_repository,
    p.UserRepository: UserRepository,
    p.FriendsRepository: FriendsRepository,
    p.StatsRepository: StatsRepository,
    p.LobbyRepository: _get_lobby_repository,
    p.BoardGenerator: LocalBoardGenerator,
    p.PendingBoardsStore: _get_pending_boards_store,
    p.NotificationSystem: _get_notification_system,
    p.GameTransportFactory: _get_game_transport_factory,
    p.Scheduler: get_scheduler,
    BackgroundBoardPersister: BackgroundBoardPersister,
}

for protocol, impl in registry.items():
    registry[protocol] = Depends(impl)
