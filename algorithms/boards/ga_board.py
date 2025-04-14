from algorithms.boards.random_board import RandomBoard
from algorithms.boards.functions.all_fields import all_fields
import random


class GABoard(RandomBoard):
    def __init__(
        self, rows: int, columns: int, start_field: tuple[int, int], mine_count: int
    ) -> None:
        RandomBoard.__init__(self, rows, columns, start_field, mine_count)

    def crossover(self, board1: "GABoard", board2: "GABoard") -> None:
        self.rows = board1.rows
        self.columns = board1.columns
        self.start_field = board1.start_field
        self.mine_count = board1.mine_count

        count = len(board1.mined_fields)
        fields = set(board1.mined_fields + board2.mined_fields)
        other_fields = list(
            set(all_fields(self.rows, self.columns, self.start_field)).difference(
                fields
            )
        )
        random.shuffle(other_fields)
        fields = list(fields)
        fields.extend(other_fields[:2])
        random.shuffle(fields)
        self.mined_fields = fields[:count]
