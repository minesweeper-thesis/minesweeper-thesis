from typing import Callable

from fastapi import Depends

from backend import protocols as p
from backend.db.db import get_async_session
from backend.lib.background_handler import BackgroundRoundHandler
from backend.lib.board_generator import AsyncBoardGenerator, BackgroundBoardGenerator
from backend.lib.board_persister import BackgroundBoardPersister
from backend.lib.pending_boards import RedisPendingStore
from backend.lib.redis_client import get_redis_client
from backend.lib.scheduler import get_scheduler
from backend.lib.session_lock import SessionLock
from backend.lib.session_runtime_store import RedisSessionRuntimeStore
from backend.repositories import *


def _get_notification_system():
    from backend.lib.notification_system import get_notification_system

    return get_notification_system()


def _get_lobby_transport_factory():
    from backend.lib.lobby_transport import get_lobby_transport_factory

    return get_lobby_transport_factory()


def _get_lobby_repository(redis=Depends(get_redis_client)):
    return RedisLobbyRepository(redis)


def _get_multiplayer_repository(
    session=Depends(get_async_session), redis=Depends(get_redis_client)
):
    return RedisMultiplayerRepository(session, redis)


def _get_pending_boards_store(redis=Depends(get_redis_client)):
    return RedisPendingStore(redis)


def _get_session_runtime_store(redis=Depends(get_redis_client)):
    return RedisSessionRuntimeStore(redis)


def get_session_lock(redis=Depends(get_redis_client)) -> SessionLock:
    return SessionLock(redis)


registry: dict[type, Callable] = {
    p.BoardRepository: BoardRepository,
    p.SingleplayerRepository: SingleplayerRepository,
    p.MultiplayerRepository: _get_multiplayer_repository,
    p.UserRepository: UserRepository,
    p.FriendsRepository: FriendsRepository,
    p.StatsRepository: StatsRepository,
    p.LobbyRepository: _get_lobby_repository,
    p.SingleBoardGenerator: BackgroundBoardGenerator,
    p.MultiBoardGenerator: AsyncBoardGenerator,
    p.PendingBoardsStore: _get_pending_boards_store,
    p.SessionRuntimeStore: _get_session_runtime_store,
    p.NotificationSystem: _get_notification_system,
    p.LobbyTransportFactory: _get_lobby_transport_factory,
    p.Scheduler: get_scheduler,
    BackgroundBoardPersister: BackgroundBoardPersister,
    BackgroundRoundHandler: BackgroundRoundHandler,
    SessionLock: get_session_lock,
}

for protocol, impl in registry.items():
    registry[protocol] = Depends(impl)
