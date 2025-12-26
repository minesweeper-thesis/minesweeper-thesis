from typing import Annotated

import backend.protocols as p
from backend.di.providers import registry
from backend.lib.background_handler import BackgroundRoundHandler
from backend.lib.board_persister import BackgroundBoardPersister

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

BoardGeneratorDep = Annotated[p.BoardGenerator, registry[p.BoardGenerator]]
PendingBoardsStoreDep = Annotated[p.PendingBoardsStore, registry[p.PendingBoardsStore]]
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

__all__ = [
    "BoardRepositoryDep",
    "SingleplayerRepositoryDep",
    "MultiplayerRepositoryDep",
    "UserRepositoryDep",
    "FriendsRepositoryDep",
    "StatsRepositoryDep",
    "LobbyRepositoryDep",
    "BoardGeneratorDep",
    "PendingBoardsStoreDep",
    "NotificationSystemDep",
    "LobbyTransportFactoryDep",
    "SchedulerDep",
    "BoardPersisterDep",
    "BackgroundRoundHandlerDep",
]
