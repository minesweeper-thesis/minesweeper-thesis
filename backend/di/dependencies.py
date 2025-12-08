from typing import Annotated

import backend.protocols as p
from backend.di.providers import registry

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
GameTransportFactoryDep = Annotated[
    p.GameTransportFactory, registry[p.GameTransportFactory]
]
SchedulerDep = Annotated[p.Scheduler, registry[p.Scheduler]]

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
    "GameTransportFactoryDep",
    "SchedulerDep",
]
