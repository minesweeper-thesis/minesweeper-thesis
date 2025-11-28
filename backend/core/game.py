import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional, Protocol

from backend.core.board import DifficultyLevel

type GameStatus = Literal["not_started", "in_progress", "finished"]
type GameResult = Literal["win", "loss"]
type GameMode = Literal["normal", "hardcore"]
type Cell = tuple[int, int]
type RevealedCell = tuple[int, int, int]


class ActionResult(ABC):
    pass


@dataclass
class RevealResult(ActionResult):
    revealed_cells: list[RevealedCell]
    game_status: GameStatus


@dataclass
class FlagResult(ActionResult):
    game_status: GameStatus = "in_progress"


@dataclass
class RemoveFlagResult(ActionResult):
    game_status: GameStatus = "in_progress"


@dataclass
class HintResult(ActionResult):
    safe_cells: list[Cell]
    game_status: GameStatus = "in_progress"


@dataclass
class LossCause:
    type: Literal["mine_clicked", "unsafe_move", "time_out"]
    cell: Optional[tuple[int, int]] = None


@dataclass
class GameStateResult(ActionResult):
    board_id: uuid.UUID
    difficulty_level: DifficultyLevel
    status: GameStatus
    result: Optional[Literal["win", "loss"]]
    revealed_cells: list[RevealedCell]
    flagged_cells: list[Cell]
    elapsed_time: float
    start_field: Cell
    loss_cause: Optional[LossCause] = None


@dataclass
class GameOverResult(ActionResult):
    result: Literal["win", "loss"]
    full_board: list[list[int]]
    elapsed_time: float
    loss_cause: Optional[LossCause] = None


type IsGameOver = bool


class Gameplay(Protocol):
    def reveal_one(self, x: int, y: int) -> ActionResult: ...
    def reveal_many(self, x: int, y: int) -> ActionResult: ...
    def flag(self, x: int, y: int) -> ActionResult: ...
    def remove_flag(self, x: int, y: int) -> ActionResult: ...
    def use_hint(self) -> ActionResult: ...
    def is_game_over(self) -> bool: ...
    def get_game_state(self) -> GameStateResult: ...


class GameAction(ABC):
    @abstractmethod
    def handle(self, gameplay: Gameplay) -> "ActionResult": ...


class GameStateAction(GameAction):
    def handle(self, gameplay: Gameplay) -> "ActionResult":
        return gameplay.get_game_state()


class HintAction(GameAction):
    def handle(self, gameplay: Gameplay) -> "ActionResult":
        return gameplay.use_hint()


class RevealOneAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> "ActionResult":
        x, y = self.cell
        return gameplay.reveal_one(x, y)


class RevealManyAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> "ActionResult":
        x, y = self.cell
        return gameplay.reveal_many(x, y)


class FlagAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> "ActionResult":
        x, y = self.cell
        return gameplay.flag(x, y)


class RemoveFlagAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> "ActionResult":
        x, y = self.cell
        return gameplay.remove_flag(x, y)


class InvalidAction(Exception):
    pass
