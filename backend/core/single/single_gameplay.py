import time
import uuid
from typing import Optional

from algorithms.boards.functions.moore import moore_neighborhood
from algorithms.boards.grid import Grid
from algorithms.checker.hint_generator import HintGenerator
from backend.core.board import Board
from backend.core.game import *


class SingleplayerGameplay(Gameplay):
    def __init__(
        self,
        id: uuid.UUID,
        board: Board,
        revealed_cells: list[Cell] = None,  # type: ignore
        flagged_cells: list[Cell] = None,  # type: ignore
        status: GameStatus = "not_started",
        result: Optional[GameResult] = None,
        used_hints: bool = False,
        elapsed_time: float = 0,
        mode: GameMode = "normal",
    ):
        if revealed_cells is None:
            revealed_cells = []

        if flagged_cells is None:
            flagged_cells = []

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
        self.game_mode: GameMode = mode
        self.revealed_cells: list[RevealedCell] = []
        self.loss_cause: Optional[LossCause] = None

        for i, j in revealed_cells:
            self.grid.revealed[i][j] = True
            self.revealed_cells.append((i, j, self.grid.grid[i][j]))

        for i, j in flagged_cells:
            self.grid.flagged[i][j] = True

        if len(revealed_cells) or len(flagged_cells):
            self._start_game_if_not_started()

    def _get_safe_cells(self) -> list[tuple[int, int]]:
        safe_cells = HintGenerator.get_safe_fields_no_cache(self.grid)

        start_x, start_y = self.start_field
        if not self.grid.revealed[start_x][start_y]:
            safe_cells.append((start_x, start_y))

        return safe_cells

    def use_hint(self) -> Optional[Cell]:
        self._start_game_if_not_started()
        self.used_hints = True
        return self._get_safe_cells()[0] if self._get_safe_cells() else None

    def _start_game_if_not_started(self):
        if self.status == "not_started":
            self.status = "in_progress"

        if self._time_start is None:
            self._time_start = time.monotonic()

    def update_elapsed_time(self):
        if self._time_start is None:
            raise RuntimeError("Game not started")

        self.elapsed_time += time.monotonic() - self._time_start

    def _finish_game(self, result: GameResult, loss_cause: Optional[LossCause] = None):
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

    def reveal_one(self, cell: Cell) -> RevealedCell:
        x, y = cell
        self._start_game_if_not_started()
        self._validate_coords(x, y)
        self._reset_revealed()

        if self.grid.flagged[x][y] or self.grid.revealed[x][y]:
            raise InvalidAction("Field is already revealed or flagged")

        if self.game_mode == "hardcore":
            if (x, y) not in self._get_safe_cells():
                self._finish_game("loss", LossCause(type="unsafe_move", cell=(x, y)))

        old_revealed = set(self.get_revealed_cells())
        self.grid.handle_field_click((x, y))

        revealed_delta = list(set(self.get_revealed_cells()) - old_revealed)

        self._update_result(revealed_delta)
        self._update_revealed_cells(revealed_delta)

        return x, y, self.grid.grid[x][y]

    def reveal_many(self, cell: Cell) -> list[RevealedCell]:
        x, y = cell
        self._start_game_if_not_started()
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

        revealed_delta = list(set(self.get_revealed_cells()) - old_revealed)

        self._update_result(revealed_delta)
        self._update_revealed_cells(revealed_delta)

        return self.revealed_cells

    def _update_result(self, revealed_delta: list[Cell]):
        for x, y in revealed_delta:
            if self.grid.grid[x][y] == -1:
                loss_cause = LossCause(type="mine_clicked", cell=(x, y))
                self._finish_game("loss", loss_cause=loss_cause)
                return

        if self.grid.check_win():
            self._finish_game("win")

    def _reset_revealed(self):
        self.revealed_cells = []

    def _update_revealed_cells(self, revealed_delta: list[Cell]):
        self.revealed_cells = sorted(
            (x, y, self.grid.grid[x][y]) for (x, y) in revealed_delta
        )

    def get_flagged_cells(self) -> list[Cell]:
        return [
            (i, j)
            for i in range(self.grid.rows)
            for j in range(self.grid.columns)
            if self.grid.flagged[i][j]
        ]

    def get_game_state(self) -> GameState:
        return GameState(
            board_id=self.board.id,
            difficulty_level=self.board.difficulty_level,
            status=self.status,
            result=self.result,
            revealed_cells=self.revealed_cells,
            flagged_cells=self.get_flagged_cells(),
            elapsed_time=self.elapsed_time,
            loss_cause=self.loss_cause,
            start_field=self.start_field,
        )

    def flag(self, cell: Cell) -> None:
        x, y = cell
        self._start_game_if_not_started()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = True

    def remove_flag(self, cell: Cell) -> None:
        x, y = cell
        self._start_game_if_not_started()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = False


__all__ = ["SingleplayerGameplay"]
