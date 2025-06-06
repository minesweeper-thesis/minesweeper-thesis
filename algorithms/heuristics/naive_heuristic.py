from algorithms.heuristics.heuristic import Heuristic
from algorithms.boards.board import Board
from algorithms.boards.random_board import RandomBoard
from algorithms.classifiers.classifier import Classifier


class NaiveHeuristic(Heuristic):
    def __init__(
        self,
        classifier: Classifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        
        tries: int,
    ) -> None:
        Heuristic.__init__(self, classifier, rows, columns, start_field, mine_count)
        self.tries = tries

    def run(self) -> Board:
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

        return best_board
