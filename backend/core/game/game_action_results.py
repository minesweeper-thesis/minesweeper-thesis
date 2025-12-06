from dataclasses import dataclass
from typing import Literal, Optional

from backend.core.game.types import *


@dataclass
class RevealResult:
    revealed_cells: list[RevealedCell]
    game_status: GameStatus


@dataclass
class FlagResult:
    game_status: GameStatus = "in_progress"


@dataclass
class RemoveFlagResult:
    game_status: GameStatus = "in_progress"


@dataclass
class HintResult:
    safe_cells: list[Cell]
    game_status: GameStatus = "in_progress"


@dataclass
class GameOverResult:
    result: Literal["win", "loss"]
    full_board: list[list[int]]
    elapsed_time: float
    loss_cause: Optional[LossCause] = None


type GameActionResult = RevealResult | FlagResult | RemoveFlagResult | HintResult | GameOverResult

__all__ = [
    "RevealResult",
    "FlagResult",
    "RemoveFlagResult",
    "HintResult",
    "GameOverResult",
    "GameActionResult",
]
