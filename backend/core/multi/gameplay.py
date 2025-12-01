import uuid
from dataclasses import dataclass
from typing import Callable, Optional

from backend.core.board import Board
from backend.core.game import *
from backend.core.single.gameplay import SingleplayerGameplay


@dataclass
class OpponentState:
    revealed_cnt: int
    result: Optional[GameResult]


type Notifier = Callable[[OpponentState], None]


class MultiplayerGameplay(Gameplay):
    def __init__(
        self,
        user_id: uuid.UUID,
        board: Board,
        mode: GameMode,
        notify_opponents: Notifier,
        revealed_cells: list[Cell] = [],
        flagged_cells: list[Cell] = [],
        status: GameStatus = "not_started",
        result: Optional[GameResult] = None,
        elapsed_time: float = 0,
    ):
        self.user_id = user_id
        self.notify_opponents = notify_opponents

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
    def revealed_cells(self) -> list[tuple[int, int]]:
        return self._gameplay.get_revealed_cells()

    @property
    def board(self) -> Board:
        return self._gameplay.board

    @property
    def mode(self) -> GameMode:
        return self._gameplay.game_mode

    @property
    def loss_cause(self) -> Optional[LossCause]:
        return self._gameplay.loss_cause

    def _notify_opponents(self):
        my_state = OpponentState(
            revealed_cnt=len(self._gameplay.get_revealed_cells()),
            result=self._gameplay.result,
        )
        self.notify_opponents(my_state)

    def reveal_one(self, x: int, y: int):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        result = self._gameplay.reveal_one(x, y)
        self._notify_opponents()
        return result

    def reveal_many(self, x: int, y: int):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        result = self._gameplay.reveal_many(x, y)
        self._notify_opponents()
        return result

    def flag(self, x: int, y: int):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.flag(x, y)

    def remove_flag(self, x: int, y: int):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.remove_flag(x, y)

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
