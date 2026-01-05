from typing import Annotated

import backend.protocols as p
from backend.di.providers import registry
from backend.lib.background_handler import BackgroundRoundHandler
from backend.lib.board_persister import BackgroundBoardPersister
from backend.lib.session_lock import SessionLock

BoardRepositoryDep = Annotated[p.BoardRepository, registry[p.BoardRepository]]
SingleplayerRepositoryDep = Annotated[
    p.SingleplayerRepository, registry[p.SingleplayerRepository]
]
MultiplayerRepositoryDep = Annotated[
    p.MultiplayerRepository, registry[p.MultiplayerRepository]
]
UserRepositoryDep = Annotated[p.UserRepository, registry[p.UserRepository]]
FriendsRepositoryDep = Annotated[p.FriendsRepository, registry[p.FriendsRepository]]
StatsRepositoryDep = Annotated[p.StatsRepository, registry[p.StatsRepository]]
LobbyRepositoryDep = Annotated[p.LobbyRepository, registry[p.LobbyRepository]]
SingleBoardGeneratorDep = Annotated[
    p.SingleBoardGenerator, registry[p.SingleBoardGenerator]
]
MultiBoardGeneratorDep = Annotated[
    p.MultiBoardGenerator, registry[p.MultiBoardGenerator]
]
PendingBoardsStoreDep = Annotated[p.PendingBoardsStore, registry[p.PendingBoardsStore]]
SessionRuntimeStoreDep = Annotated[
    p.SessionRuntimeStore, registry[p.SessionRuntimeStore]
]
NotificationSystemDep = Annotated[p.NotificationSystem, registry[p.NotificationSystem]]
LobbyTransportFactoryDep = Annotated[
    p.LobbyTransportFactory, registry[p.LobbyTransportFactory]
]
SchedulerDep = Annotated[p.Scheduler, registry[p.Scheduler]]
BoardPersisterDep = Annotated[
    BackgroundBoardPersister, registry[BackgroundBoardPersister]
]
BackgroundRoundHandlerDep = Annotated[
    BackgroundRoundHandler, registry[BackgroundRoundHandler]
]
SessionLockDep = Annotated[SessionLock, registry[SessionLock]]


__all__ = [
    "BoardRepositoryDep",
    "SingleplayerRepositoryDep",
    "MultiplayerRepositoryDep",
    "UserRepositoryDep",
    "FriendsRepositoryDep",
    "StatsRepositoryDep",
    "LobbyRepositoryDep",
    "SingleBoardGeneratorDep",
    "MultiBoardGeneratorDep",
    "PendingBoardsStoreDep",
    "NotificationSystemDep",
    "LobbyTransportFactoryDep",
    "SchedulerDep",
    "BoardPersisterDep",
    "BackgroundRoundHandlerDep",
    "SessionRuntimeStoreDep",
    "SessionLockDep",
]
