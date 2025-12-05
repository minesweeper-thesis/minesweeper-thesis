import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.game.types import *


@dataclass
class SessionScoreItem:
    user_id: uuid.UUID
    score: float


@dataclass
class SessionScoreboard:
    items: list[SessionScoreItem]

    def sort(self) -> None:
        self.items = sorted(self.items, key=lambda item: item.score, reverse=True)


@dataclass
class RoundScoreItem:
    user_id: uuid.UUID
    score: float
    revealed_count: int
    status: GameStatus
    result: Optional[GameResult] = None
    loss_cause: Optional[LossCause] = None


def key_func(item: RoundScoreItem):
    loss_cause = item.loss_cause.type if item.loss_cause else None
    return item.score, item.revealed_count, item.result == "win", loss_cause


@dataclass
class RoundScoreboard:
    items: list[RoundScoreItem]

    def sort(self) -> None:
        self.items = sorted(self.items, key=key_func, reverse=True)


__all__ = [
    "SessionScoreItem",
    "SessionScoreboard",
    "RoundScoreItem",
    "RoundScoreboard",
]
