from algorithms.boards.board import Board
from algorithms.boards.functions.all_fields import all_fields
import random


class SemiRandomBoard(Board):
    """Board with randomly mined boards except for some initial mined boards."""

    def __init__(
        self,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        already_mined_fields: list[tuple[int, int]],
    ) -> None:
        """Initializes board with randomly mined fields except for some initial mined boards.

        Args:
            rows (int): number of rows of the board.
            columns (int): number of columns of the board.
            start_field (tuple[int, int]): coordinates of the first clicked field on the board.
            mine_count (int): number of mines on the board.
            already_mined_fields (list[tuple[int, int]]): list of fields that are already mined.
        """
        fields = all_fields(rows, columns, start_field, already_mined_fields)
        random.shuffle(fields)
        fields = [field for field in fields if field > already_mined_fields[-1]]

        if len(already_mined_fields) > mine_count:
            already_mined_fields = already_mined_fields[:mine_count]

        mined_fields = (
            already_mined_fields + fields[: mine_count - len(already_mined_fields)]
        )
        Board.__init__(self, rows, columns, start_field, mine_count, mined_fields)
