from algorithms.boards.board import Board
from algorithms.boards.functions.all_fields import all_fields
import random


class RandomBoard(Board):
    def __init__(
        self, rows: int, columns: int, start_field: tuple[int, int], mine_count: int
    ) -> None:
        fields = all_fields(rows, columns, start_field)
        random.shuffle(fields)
        Board.__init__(
            self, rows, columns, start_field, mine_count, fields[:mine_count]
        )
