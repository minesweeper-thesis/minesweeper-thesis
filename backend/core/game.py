from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional, Protocol

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
    game_status: Literal["in_progress"] = "in_progress"


@dataclass
class HintResult(ActionResult):
    safe_cells: list[Cell]
    game_status: Literal["in_progress"] = "in_progress"


@dataclass
class LossCause:
    type: Literal["mine_clicked", "unsafe_move"]
    cell: tuple[int, int]


@dataclass
class GameStateResult(ActionResult):
    status: GameStatus
    result: Optional[Literal["win", "loss"]]
    revealed_cells: list[RevealedCell]
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
    def handle(self, gameplay: Gameplay) -> tuple["ActionResult", IsGameOver]: ...


class GameStateAction(GameAction):
    def handle(self, gameplay: Gameplay) -> tuple["ActionResult", IsGameOver]:
        return gameplay.get_game_state(), gameplay.is_game_over()


class HintAction(GameAction):
    def handle(self, gameplay: Gameplay) -> tuple["ActionResult", IsGameOver]:
        return gameplay.use_hint(), gameplay.is_game_over()


class RevealOneAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> tuple["ActionResult", IsGameOver]:
        x, y = self.cell
        return gameplay.reveal_one(x, y), gameplay.is_game_over()


class RevealManyAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> tuple["ActionResult", IsGameOver]:
        x, y = self.cell
        return gameplay.reveal_many(x, y), gameplay.is_game_over()


class FlagAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> tuple["ActionResult", IsGameOver]:
        x, y = self.cell
        return gameplay.flag(x, y), gameplay.is_game_over()


class RemoveFlagAction(GameAction):
    cell: tuple[int, int]

    def __init__(self, cell: tuple[int, int]):
        self.cell = cell

    def handle(self, gameplay: Gameplay) -> tuple["ActionResult", IsGameOver]:
        x, y = self.cell
        return gameplay.remove_flag(x, y), gameplay.is_game_over()


class InvalidAction(Exception):
    pass
