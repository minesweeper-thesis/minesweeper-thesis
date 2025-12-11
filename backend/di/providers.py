from typing import Callable

from fastapi import Depends

from backend import protocols as p
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


registry: dict[type, Callable] = {
    p.BoardRepository: BoardRepository,
    p.SingleplayerRepository: SingleplayerRepository,
    p.MultiplayerRepository: MultiplayerRepository,
    p.UserRepository: UserRepository,
    p.FriendsRepository: FriendsRepository,
    p.StatsRepository: StatsRepository,
    p.LobbyRepository: LobbyRepository,
    p.BoardGenerator: LocalBoardGenerator,
    p.PendingBoardsStore: get_pending_boards_store,
    p.NotificationSystem: _get_notification_system,
    p.GameTransportFactory: _get_game_transport_factory,
    p.Scheduler: get_scheduler,
}

for protocol, impl in registry.items():
    registry[protocol] = Depends(impl)
