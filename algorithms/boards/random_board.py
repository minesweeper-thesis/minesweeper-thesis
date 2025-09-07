from algorithms.boards.board import Board
from algorithms.boards.functions.all_fields import all_fields
import random


class RandomBoard(Board):
    """Board with randomly mined fields."""

    def __init__(
        self, rows: int, columns: int, start_field: tuple[int, int], mine_count: int
    ) -> None:
        """Initializes board with randomly mined fields.

        Args:
            rows (int): number of rows of the board.
            columns (int): number of columns of the board.
            start_field (tuple[int, int]): coordinates of the first clicked field on the board.
            mine_count (int): number of mines on the board.
        """
        fields = all_fields(rows, columns, start_field, [])
        random.shuffle(fields)
        Board.__init__(
            self, rows, columns, start_field, mine_count, fields[:mine_count]
        )
