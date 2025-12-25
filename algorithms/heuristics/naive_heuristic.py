from algorithms.boards.base_board import BaseBoard
from algorithms.boards.random_board import RandomBoard
from algorithms.classifiers.base_classifier import BaseClassifier
from algorithms.heuristics.base_heuristic import BaseHeuristic


class NaiveHeuristic(BaseHeuristic):
    def __init__(
        self,
        classifier: BaseClassifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        tries: int,
    ) -> None:
        BaseHeuristic.__init__(self, classifier, rows, columns, start_field, mine_count)
        self.tries = tries

    def run(self) -> BaseBoard:
        best_score = 0
        best_board = None

        for _ in range(self.tries):
            board = RandomBoard(
                self.rows, self.columns, self.start_field, self.mine_count
            )
            score = self.classifier.classify(board)
            if score > best_score:
                best_score = score
                best_board = board

        return best_board if best_board is not None else board
