import uuid

from algorithms.boards.functions.moore import moore_neighborhood
from algorithms.boards.grid import Grid


class SingleplayerGameplay:
    def __init__(
        self,
        gameplay_id: uuid.UUID,
        grid: Grid,
    ):
        self.gameplay_id = gameplay_id
        self.time: float = 0.0
        self.used_prompts: bool = False
        self.grid: Grid = grid

    def _check_win(self) -> bool:
        return self.grid.check_win()

    def _get_revealed(self):
        return {
            (i, j)
            for i in range(self.grid.rows)
            for j in range(self.grid.columns)
            if self.grid.revealed[i][j]
        }

    def reveal_one(self, x: int, y: int) -> dict:
        if x < 0 or y < 0 or x >= self.grid.rows or y >= self.grid.columns:
            raise IndexError("Field out of bounds")

        if self.grid.flagged[x][y] or self.grid.revealed[x][y]:
            return {
                "game_state": "in_progress",
            }

        self._revealed = self._get_revealed()
        self.grid.handle_field_click((x, y))

        newly = self._get_revealed() - self._revealed
        revealed_cells = [
            {"x": i, "y": j, "value": self.grid.grid[i][j]} for (i, j) in newly
        ]

        if self.grid.grid[x][y] == -1:
            return {
                "game_state": "lost",
                "full_board": self.grid.grid,
            }

        if self._check_win():
            return {
                "game_state": "won",
                "full_board": self.grid.grid,
            }

        return {
            "revealed_cells": revealed_cells,
            "game_state": "in_progress",
        }

    def reveal_many(self, x: int, y: int) -> dict:
        if not (0 <= x < self.grid.rows and 0 <= y < self.grid.columns):
            raise IndexError("Field out of bounds")

        if not self.grid.revealed[x][y]:
            return {
                "game_state": "in_progress",
            }

        neighbors = moore_neighborhood((x, y), self.grid.rows, self.grid.columns)
        flagged_count = sum(1 for (nx, ny) in neighbors if self.grid.flagged[nx][ny])

        if flagged_count != self.grid.grid[x][y]:
            return {
                "game_state": "in_progress",
            }

        self._revealed = self._get_revealed()

        for nx, ny in neighbors:
            if not self.grid.flagged[nx][ny] and not self.grid.revealed[nx][ny]:
                self.grid.handle_field_click((nx, ny))

        newly = self._get_revealed() - self._revealed
        revealed_cells = [
            {"x": i, "y": j, "value": self.grid.grid[i][j]} for (i, j) in newly
        ]

        for x, y in newly:
            if self.grid.grid[x][y] == -1:
                return {
                    "game_state": "lost",
                    "full_board": self.grid.grid,
                }

        if self._check_win():
            return {
                "game_state": "won",
                "full_board": self.grid.grid,
            }

        return {
            "revealed_cells": revealed_cells,
            "game_state": "in_progress",
        }

    def flag(self, x: int, y: int) -> dict:
        """Set a flag on an unrevealed cell."""
        if x < 0 or y < 0 or x >= self.grid.rows or y >= self.grid.columns:
            raise IndexError("Field out of bounds")

        self.grid.flagged[x][y] = True

        return {"game_state": "in_progress"}

    def remove_flag(self, x: int, y: int) -> dict:
        if x < 0 or y < 0 or x >= self.grid.rows or y >= self.grid.columns:
            raise IndexError("Field out of bounds")

        self.grid.flagged[x][y] = False

        return {"game_state": "in_progress"}
