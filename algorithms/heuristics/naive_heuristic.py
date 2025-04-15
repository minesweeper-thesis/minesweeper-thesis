from algorithms.heuristics.heuristic import Heuristic
from algorithms.boards.board import Board
from algorithms.boards.random_board import RandomBoard


class NaiveHeuristic(Heuristic):
    def __init__(
        self, rows: int, columns: int, start_field: tuple[int, int], mine_count: int
    ) -> None:
        Heuristic.__init__(self, None, rows, columns, start_field, mine_count)

    def run(self) -> Board:
        return RandomBoard(self.rows, self.columns, self.start_field, self.mine_count)
