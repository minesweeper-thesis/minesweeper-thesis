import numpy as np
from typing import Callable
from algorithms.boards.grid import Grid


class Board:
    """Board of the Minesweeper game."""

    def __init__(
        self,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        mined_fields: list[tuple[int, int]],
    ) -> None:
        """Initializes with basic parameters.

        Args:
            rows (int): number of rows of the board.
            columns (int): number of columns of the board.
            start_field (tuple[int, int]): coordinates of the first clicked field on the board.
            mine_count (int): number of mines on the board.
            mined_fields (list[tuple[int, int]]): list of mined fields.
        """
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count
        self.mined_fields = mined_fields

    def grid(self) -> Grid:
        """Returns grid of the board.

        Returns:
            Grid: grid of the board.
        """
        return Grid(self.rows, self.columns, self.mined_fields)

    def __transform(
        self, function: Callable[[tuple[int, int]], tuple[int, int]]
    ) -> "Board":
        """Transforms the board with some function.

        Args:
            function (Callable[[tuple[int, int]], tuple[int, int]]): transformation.

        Returns:
            Board: transformed board.
        """
        start_field = function(self.start_field)
        mined_fields = [function(field) for field in self.mined_fields]

        return Board(
            self.rows, self.columns, start_field, self.mine_count, mined_fields
        )

    def symmetries(self) -> tuple["Board"]:
        """Returns all the symmetries of the board.

        Returns:
            tuple[Board]: symmetric boards, including the current one.
        """
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
        """Returns the board represented as input suitable for ML models.

        Returns:
            np.ndarray: board.
        """
        mined = [[0 for _ in range(self.columns)] for _ in range(self.rows)]
        for i, j in self.mined_fields:
            mined[i][j] = 1

        grid = self.grid()
        grid.handle_field_click(self.start_field)

        return np.array([mined, grid.revealed])

    def to_json(self) -> dict:
        """Returns json representation of the board.

        Returns:
            dict: json representation of the board.
        """
        return {
            "rows": self.rows,
            "columns": self.columns,
            "start_field": list(self.start_field),
            "mine_count": self.mine_count,
            "mined_fields": [list(pos) for pos in self.mined_fields],
        }
