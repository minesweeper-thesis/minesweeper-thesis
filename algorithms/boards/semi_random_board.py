from algorithms.boards.board import Board
from algorithms.boards.functions.all_fields import all_fields
import random


class SemiRandomBoard(Board):
    def __init__(
        self,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        already_mined_fields: list[tuple[int, int]],
    ) -> None:
        fields = all_fields(rows, columns, start_field, already_mined_fields)
        random.shuffle(fields)

        if len(already_mined_fields) > mine_count:
            already_mined_fields = already_mined_fields[:mine_count]

        mined_fields = (
            already_mined_fields + fields[: mine_count - len(already_mined_fields)]
        )
        Board.__init__(self, rows, columns, start_field, mine_count, mined_fields)
