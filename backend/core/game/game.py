import enum
import time
from typing import Optional

from algorithms.boards.functions.moore import moore_neighborhood
from algorithms.boards.grid import Grid
from algorithms.checker.hint_generator import HintGenerator


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
        grid: Grid,
        revealed_cells: list[tuple[int, int]],
        game_status: GameStatus,
        game_result: Optional[GameResult],
        used_hints: bool = False,
        elapsed_time: float = 0,
    ):
        self._started = False
        self._time_start = None
        self.elapsed_time: float = elapsed_time
        self.used_hints: bool = used_hints
        self.grid: Grid = grid
        for i, j in revealed_cells:
            self.grid.revealed[i][j] = True
        self.status: GameStatus = game_status
        self.result: Optional[GameResult] = game_result

    def use_hint(self) -> list[tuple[int, int]]:
        self.start_game_if_first_action()
        self.used_hints = True
        return HintGenerator.get_safe_fields_no_cache(self.grid)

    def start_game_if_first_action(self):
        if not self._started:
            self._started = True
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
        if self._started:
            self._started = False
        else:
            raise RuntimeError("Game not started")

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

    def reveal_one(self, x: int, y: int) -> list[tuple[int, int, int]]:
        self.start_game_if_first_action()
        self._validate_coords(x, y)

        if self.grid.flagged[x][y] or self.grid.revealed[x][y]:
            raise InvalidAction("Field is already revealed or flagged")

        old_revealed = set(self.get_revealed_cells())
        self.grid.handle_field_click((x, y))
        new_revealed = set(self.get_revealed_cells()) - old_revealed

        return self._get_reveal_return_value(list(new_revealed))

    def reveal_many(self, x: int, y: int) -> list[tuple[int, int, int]]:
        self.start_game_if_first_action()
        self._validate_coords(x, y)

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

        new_revealed = set(self.get_revealed_cells()) - old_revealed

        return self._get_reveal_return_value(list(new_revealed))

    def _get_reveal_return_value(
        self, new_revealed: list[tuple[int, int]]
    ) -> list[tuple[int, int, int]]:
        for x, y in new_revealed:
            if self.grid.grid[x][y] == -1:
                self.finish_game(GameResult.loss)

        if self.grid.check_win():
            self.finish_game(GameResult.win)

        return [(x, y, self.grid.grid[x][y]) for (x, y) in new_revealed]

    def flag(self, x: int, y: int):
        self.start_game_if_first_action()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = True

    def remove_flag(self, x: int, y: int):
        self.start_game_if_first_action()
        self._validate_coords(x, y)

        self.grid.flagged[x][y] = False
