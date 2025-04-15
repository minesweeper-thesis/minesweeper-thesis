import numpy as np
from typing import Callable
from algorithms.boards.grid import Grid
import math


class Board:
    def __init__(
        self,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        mined_fields: list[tuple[int, int]],
    ) -> None:
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count
        self.mined_fields = mined_fields

    def grid(self) -> Grid:
        return Grid(self.rows, self.columns, self.mined_fields)

    def __transform(
        self, function: Callable[[tuple[int, int]], tuple[int, int]]
    ) -> "Board":
        start_field = function(self.start_field)
        mined_fields = [function(field) for field in self.mined_fields]

        return Board(
            self.rows, self.columns, start_field, self.mine_count, mined_fields
        )

    def symmetries(self) -> tuple["Board"]:
        if self.rows == self.columns:
            return (
                self,
                self.__transform(
                    lambda coords: (coords[0], self.columns - 1 - coords[1])
                ),
                self.__transform(lambda coords: (self.rows - 1 - coords[0], coords[1])),
                self.__transform(
                    lambda coords: (
                        self.rows - 1 - coords[0],
                        self.columns - 1 - coords[1],
                    )
                ),
                self.__transform(lambda coords: (coords[1], self.rows - 1 - coords[0])),
                self.__transform(
                    lambda coords: (
                        self.columns - 1 - coords[1],
                        self.rows - 1 - coords[0],
                    )
                ),
                self.__transform(
                    lambda coords: (self.columns - 1 - coords[1], coords[0])
                ),
                self.__transform(lambda coords: (coords[1], coords[0])),
            )

        return (
            self,
            self.__transform(lambda coords: (coords[0], self.columns - 1 - coords[1])),
            self.__transform(lambda coords: (self.rows - 1 - coords[0], coords[1])),
            self.__transform(
                lambda coords: (self.rows - 1 - coords[0], self.columns - 1 - coords[1])
            ),
        )

    def model_input(
        self,
    ) -> np.ndarray:
        mined = [[0 for _ in range(self.columns)] for _ in range(self.rows)]
        for i, j in self.mined_fields:
            mined[i][j] = 1

        grid = self.grid()
        grid.handle_field_click(self.start_field)

        return np.array([mined, grid.revealed])

    def to_json(self) -> dict:
        return {
            "rows": self.rows,
            "columns": self.columns,
            "start_field": list(self.start_field),
            "mine_count": self.mine_count,
            "mined_fields": [list(pos) for pos in self.mined_fields],
        }
