import uuid
from dataclasses import dataclass
from typing import Literal, Optional

from backend.core.board import DifficultyLevel

type GameStatus = Literal["not_started", "in_progress", "finished"]
type GameResult = Literal["win", "loss"]
type GameMode = Literal["normal", "hardcore"]
type Cell = tuple[int, int]
type RevealedCell = tuple[int, int, int]


@dataclass
class LossCause:
    type: Literal["mine_clicked", "unsafe_move", "time_out"]
    cell: Optional[Cell] = None


@dataclass
class GameState:
    board_id: uuid.UUID
    difficulty_level: DifficultyLevel
    status: GameStatus
    result: Optional[Literal["win", "loss"]]
    revealed_cells: list[RevealedCell]
    flagged_cells: list[Cell]
    elapsed_time: float
    start_field: Cell
    loss_cause: Optional[LossCause] = None


class InvalidAction(Exception):
    pass


__all__ = [
    "GameStatus",
    "GameResult",
    "GameMode",
    "Cell",
    "RevealedCell",
    "LossCause",
    "GameState",
    "InvalidAction",
]
