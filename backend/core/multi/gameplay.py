import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.board import Board
from backend.core.game import *
from backend.core.single.gameplay import SingleplayerGameplay


@dataclass
class OpponentState:
    revealed_cnt: int
    result: Optional[GameResult]


class MultiplayerGameplay(Gameplay):
    def __init__(
        self,
        user_id: uuid.UUID,
        board: Board,
        mode: GameMode,
        revealed_cells: list[Cell] = None,  # type: ignore
        flagged_cells: list[Cell] = None,  # type: ignore
        status: GameStatus = "not_started",
        result: Optional[GameResult] = None,
        elapsed_time: float = 0,
    ):
        if revealed_cells is None:
            revealed_cells = []

        if flagged_cells is None:
            flagged_cells = []

        self.user_id = user_id

        self._gameplay = SingleplayerGameplay(
            id=uuid.uuid4(),
            board=board,
            revealed_cells=revealed_cells,
            flagged_cells=flagged_cells,
            status=status,
            result=result,
            used_hints=False,
            elapsed_time=elapsed_time,
            mode=mode,
        )

    @property
    def time(self) -> float:
        return self._gameplay.elapsed_time

    @property
    def status(self) -> GameStatus:
        return self._gameplay.status

    @property
    def result(self) -> Optional[GameResult]:
        return self._gameplay.result

    @property
    def revealed_cells(self) -> list[Cell]:
        return self._gameplay.get_revealed_cells()

    @property
    def flagged_cells(self) -> list[Cell]:
        return self._gameplay.get_flagged_cells()

    @property
    def board(self) -> Board:
        return self._gameplay.board

    @property
    def mode(self) -> GameMode:
        return self._gameplay.game_mode

    @property
    def loss_cause(self) -> Optional[LossCause]:
        return self._gameplay.loss_cause

    @property
    def elapsed_time(self) -> float:
        return self._gameplay.elapsed_time

    def reveal_one(self, cell: Cell):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.reveal_one(cell)

    def reveal_many(self, cell: Cell):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.reveal_many(cell)

    def flag(self, cell: Cell):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.flag(cell)

    def remove_flag(self, cell: Cell):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.remove_flag(cell)

    def start_game_if_not_started(self):
        self._gameplay._start_game_if_not_started()

    def get_game_state(self):
        return self._gameplay.get_game_state()

    def use_hint(self):
        raise RuntimeError("Hints are not available in multiplayer mode")

    def is_game_over(self):
        return self.status == "finished"

    def finish_game(self, result: GameResult, loss_cause: Optional[LossCause] = None):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        self._gameplay._finish_game(result, loss_cause)
