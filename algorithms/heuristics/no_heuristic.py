from algorithms.boards.board import Board
from algorithms.boards.random_board import RandomBoard
from algorithms.classifiers.classifier import Classifier
from algorithms.heuristics.heuristic import Heuristic


class NoHeuristic(Heuristic):
    def __init__(
        self,
        _: Classifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
    ) -> None:
        Heuristic.__init__(self, None, rows, columns, start_field, mine_count)

    def run(self) -> Board:
        return RandomBoard(self.rows, self.columns, self.start_field, self.mine_count)
