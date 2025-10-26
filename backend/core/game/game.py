import enum
import time
from typing import Optional

from algorithms.boards.functions.moore import moore_neighborhood
from algorithms.boards.grid import Grid
from algorithms.checker.hint_generator import HintGenerator
from backend.models.board_models import Board
from backend.schemas.game_schemas import GameMode


class GameStatus(enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    finished = "finished"


class GameResult(enum.Enum):
    win = "win"
    loss = "loss"


class InvalidAction(Exception):
    pass


class SingleplayerGameplay:
    def __init__(
        self,
        board: Board,
        revealed_cells: list[tuple[int, int]],
        status: GameStatus,
        result: Optional[GameResult],
        used_hints: bool,
        elapsed_time: float,
        mode: GameMode,
    ):
        self._time_start = None

        self.grid = Grid(
            rows=board.board_type.rows,
            columns=board.board_type.columns,
            mined_fields=board.minefields,
        )
        self.start_field = board.start_field

        self.status: GameStatus = status
        self.result: Optional[GameResult] = result
        self.used_hints = used_hints
        self.elapsed_time = elapsed_time
        self.game_mode = mode
        self.revealed: list[tuple[int, int, int]] = []

        for i, j in revealed_cells:
            self.grid.revealed[i][j] = True

    def _get_safe_cells(self) -> list[tuple[int, int]]:
        safe_cells = HintGenerator.get_safe_fields_no_cache(self.grid)

        start_x, start_y = self.start_field
        if not self.grid.revealed[start_x][start_y]:
            safe_cells.append((start_x, start_y))

        return safe_cells

    def use_hint(self) -> list[tuple[int, int]]:
        self.start_game_if_first_action()
        self.used_hints = True
        return self._get_safe_cells()

    def start_game_if_first_action(self):
        if self.status == GameStatus.not_started:
            self.status = GameStatus.in_progress
            self._time_start = time.monotonic()

    def update_elapsed_time(self):
        if self._time_start is None:
            raise RuntimeError("Game not started")

        if self.elapsed_time is None:
            self.elapsed_time = time.monotonic() - self._time_start
        else:
            self.elapsed_time += time.monotonic() - self._time_start

    def finish_game(self, result: GameResult):
        if self.status == GameStatus.finished:
            return

        self.update_elapsed_time()
        self.status = GameStatus.finished
        self.result = result

    def get_revealed_cells(self):
        return [
            (i, j)
            for i in range(self.grid.rows)
            for j in range(self.grid.columns)
            if self.grid.revealed[i][j]
        ]

    def _validate_coords(self, x: int, y: int):
        if x < 0 or y < 0 or x >= self.grid.rows or y >= self.grid.columns:
            raise IndexError("Field out of bounds")

    def reveal_one(self, x: int, y: int):
        self.start_game_if_first_action()
        self._validate_coords(x, y)
        self._reset_revealed()

        if self.grid.flagged[x][y] or self.grid.revealed[x][y]:
            raise InvalidAction("Field is already revealed or flagged")

        if self.game_mode == GameMode.hardcore:
            if (x, y) not in self._get_safe_cells():
                self.finish_game(GameResult.loss)
                return

        old_revealed = set(self.get_revealed_cells())
        self.grid.handle_field_click((x, y))

        revealed = list(set(self.get_revealed_cells()) - old_revealed)

        self._update_result(revealed)
        self._set_revealed(revealed)

    def reveal_many(self, x: int, y: int):
        self.start_game_if_first_action()
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

    def _update_result(self, revealed: list[tuple[int, int]]):
        for x, y in revealed:
            if self.grid.grid[x][y] == -1:
                self.finish_game(GameResult.loss)
                return

        if self.grid.check_win():
            self.finish_game(GameResult.win)
            return

    def _reset_revealed(self):
        self.revealed = []

    def _set_revealed(self, revealed: list[tuple[int, int]]):
        self.revealed = [(x, y, self.grid.grid[x][y]) for (x, y) in revealed]

    def flag(self, x: int, y: int):
        self.start_game_if_first_action()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = True

    def remove_flag(self, x: int, y: int):
        self.start_game_if_first_action()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = False
