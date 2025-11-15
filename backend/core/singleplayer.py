import time
import uuid
from typing import Optional

from algorithms.boards.functions.moore import moore_neighborhood
from algorithms.boards.grid import Grid
from algorithms.checker.hint_generator import HintGenerator
from backend.core.board import Board
from backend.core.game import *


class SingleplayerGameplay:
    def __init__(
        self,
        id: uuid.UUID,
        board: Board,
        revealed_cells: list[tuple[int, int]] = [],
        status: GameStatus = "not_started",
        result: Optional[GameResult] = None,
        used_hints: bool = False,
        elapsed_time: float = 0,
        mode: GameMode = "normal",
    ):
        self.id = id
        self.board = board

        self._time_start = None

        self.grid = Grid(
            rows=board.difficulty_level.rows,
            columns=board.difficulty_level.columns,
            mined_fields=board.minefields,
        )
        self.start_field = board.start_field

        self.status: GameStatus = status
        self.result: Optional[GameResult] = result
        self.used_hints = used_hints
        self.elapsed_time = elapsed_time
        self.game_mode = mode
        self.revealed: list[tuple[int, int, int]] = []
        self.loss_cause: Optional[LossCause] = None

        for i, j in revealed_cells:
            self.grid.revealed[i][j] = True

    def _get_safe_cells(self) -> list[tuple[int, int]]:
        safe_cells = HintGenerator.get_safe_fields_no_cache(self.grid)

        start_x, start_y = self.start_field
        if not self.grid.revealed[start_x][start_y]:
            safe_cells.append((start_x, start_y))

        return safe_cells

    def use_hint(self) -> HintResult:
        self.start_game_if_not_started()
        self.used_hints = True
        return HintResult(safe_cells=self._get_safe_cells()[:1])

    def start_game_if_not_started(self):
        if self.status == "not_started":
            self.status = "in_progress"
            self._time_start = time.monotonic()

    def update_elapsed_time(self):
        if self._time_start is None:
            raise RuntimeError("Game not started")

        if self.elapsed_time is None:
            self.elapsed_time = time.monotonic() - self._time_start
        else:
            self.elapsed_time += time.monotonic() - self._time_start

    def finish_game(self, result: GameResult, loss_cause: Optional[LossCause] = None):
        if self.status == "finished":
            return

        self.update_elapsed_time()
        self.status = "finished"
        self.result = result
        self.loss_cause = loss_cause

    def is_game_over(self) -> bool:
        return self.status == "finished"

    def get_revealed_cells(self):
        return sorted(
            (i, j)
            for i in range(self.grid.rows)
            for j in range(self.grid.columns)
            if self.grid.revealed[i][j]
        )

    def _validate_coords(self, x: int, y: int):
        if x < 0 or y < 0 or x >= self.grid.rows or y >= self.grid.columns:
            raise IndexError("Field out of bounds")

    def reveal_one(self, x: int, y: int):
        self.start_game_if_not_started()
        self._validate_coords(x, y)
        self._reset_revealed()

        if self.grid.flagged[x][y] or self.grid.revealed[x][y]:
            raise InvalidAction("Field is already revealed or flagged")

        if self.game_mode == "hardcore":
            if (x, y) not in self._get_safe_cells():
                self.finish_game("loss", LossCause(type="unsafe_move", cell=(x, y)))
                return GameOverResult(
                    result="loss",
                    full_board=self.grid.grid,
                    elapsed_time=self.elapsed_time,
                    loss_cause=self.loss_cause,
                )

        old_revealed = set(self.get_revealed_cells())
        self.grid.handle_field_click((x, y))

        revealed = list(set(self.get_revealed_cells()) - old_revealed)

        self._update_result(revealed)
        self._set_revealed(revealed)

        if self.result is not None:
            return GameOverResult(
                result=self.result,
                full_board=self.grid.grid,
                elapsed_time=self.elapsed_time,
                loss_cause=self.loss_cause,
            )

        return RevealResult(revealed_cells=self.revealed, game_status=self.status)

    def reveal_many(self, x: int, y: int):
        self.start_game_if_not_started()
        self._validate_coords(x, y)
        self._reset_revealed()

        if not self.grid.revealed[x][y]:
            raise InvalidAction("Field must be revealed to use reveal_many")

        neighbors = moore_neighborhood((x, y), self.grid.rows, self.grid.columns)
        flagged_count = sum(1 for (nx, ny) in neighbors if self.grid.flagged[nx][ny])

        if flagged_count != self.grid.grid[x][y]:
            raise InvalidAction("Invalid flag count")

        old_revealed = set(self.get_revealed_cells())

        for nx, ny in neighbors:
            if not self.grid.flagged[nx][ny] and not self.grid.revealed[nx][ny]:
                self.grid.handle_field_click((nx, ny))

        revealed = list(set(self.get_revealed_cells()) - old_revealed)

        self._update_result(revealed)
        self._set_revealed(revealed)

        if self.result is not None:
            return GameOverResult(
                result=self.result,
                full_board=self.grid.grid,
                elapsed_time=self.elapsed_time,
                loss_cause=self.loss_cause,
            )

        return RevealResult(revealed_cells=self.revealed, game_status=self.status)

    def _update_result(self, revealed: list[tuple[int, int]]):
        for x, y in revealed:
            if self.grid.grid[x][y] == -1:
                loss_cause = LossCause(type="mine_clicked", cell=(x, y))
                self.finish_game("loss", loss_cause=loss_cause)
                return

        if self.grid.check_win():
            self.finish_game("win")
            return

    def _reset_revealed(self):
        self.revealed = []

    def _set_revealed(self, revealed: list[tuple[int, int]]):
        self.revealed = sorted((x, y, self.grid.grid[x][y]) for (x, y) in revealed)

    def get_game_state(self) -> GameStateResult:
        return GameStateResult(
            status=self.status,
            result=self.result,
            revealed_cells=self.revealed,
            elapsed_time=self.elapsed_time,
            loss_cause=self.loss_cause,
            start_field=self.start_field,
        )

    def flag(self, x: int, y: int):
        self.start_game_if_not_started()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = True

        return FlagResult()

    def remove_flag(self, x: int, y: int):
        self.start_game_if_not_started()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = False

        return FlagResult()
