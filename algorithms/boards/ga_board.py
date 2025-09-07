from algorithms.boards.random_board import RandomBoard
from algorithms.boards.functions.all_fields import all_fields
import random


class GABoard(RandomBoard):
    """Board adjusted to the genetic algorithm heuristic."""

    def __init__(
        self, rows: int, columns: int, start_field: tuple[int, int], mine_count: int
    ) -> None:
        """Initializes the board as a random one.

        Args:
            rows (int): number of rows of the board.
            columns (int): number of columns of the board.
            start_field (tuple[int, int]): coordinates of the first clicked field on the board.
            mine_count (int): number of mines on the board.
        """
        RandomBoard.__init__(self, rows, columns, start_field, mine_count)

    def crossover(self, board1: "GABoard", board2: "GABoard") -> None:
        """Replaces the board with a board that is the result of the crossover between board1 and board2.

        Args:
            board1 (GABoard): first parent board.
            board2 (GABoard): second parent board.
        """
        self.rows = board1.rows
        self.columns = board1.columns
        self.start_field = board1.start_field
        self.mine_count = board1.mine_count

        fields = list(set(board1.mined_fields).union(set(board2.mined_fields)))
        other_fields = all_fields(self.rows, self.columns, self.start_field, fields)

        random.shuffle(other_fields)
        fields.extend(other_fields[:2])
        random.shuffle(fields)
        self.mined_fields = fields[: self.mine_count]
