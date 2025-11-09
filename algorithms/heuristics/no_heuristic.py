from algorithms.boards.base_board import BaseBoard
from algorithms.boards.random_board import RandomBoard
from algorithms.classifiers.base_classifier import BaseClassifier
from algorithms.heuristics.heuristic import BaseHeuristic


class NoHeuristic(BaseHeuristic):
    def __init__(
        self,
        _: BaseClassifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
    ) -> None:
        BaseHeuristic.__init__(self, None, rows, columns, start_field, mine_count)

    def run(self) -> BaseBoard:
        return RandomBoard(self.rows, self.columns, self.start_field, self.mine_count)
