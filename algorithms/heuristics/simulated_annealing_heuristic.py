from algorithms.heuristics.heuristic import Heuristic
from algorithms.boards.board import Board
from algorithms.boards.random_board import RandomBoard
from algorithms.boards.random_neighbour_board import RandomNeighbourBoard
from algorithms.classifiers.classifier import Classifier
import math
import random


class SimulatedAnnealingHeuristic(Heuristic):
    def __init__(
        self,
        classifier: Classifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        iterations: int,
        fields_changed: int,
        T_MAX: float = 100.0,
        T_MIN: float = 1e-3,
    ) -> None:
        Heuristic.__init__(self, classifier, rows, columns, start_field, mine_count)
        self.iterations = iterations
        self.fields_changed = fields_changed
        self.T_MAX = T_MAX
        self.T_MIN = T_MIN

    def run(self) -> Board:
        best_board = None
        best_score = 0.0
        board = RandomBoard(self.rows, self.columns, self.start_field, self.mine_count)
        score = self.classifier.classify(board)

        if self.iterations > 1:
            alpha = (self.T_MIN / self.T_MAX) ** (1 / (self.iterations - 1))
        else:
            alpha = 1

        t = self.T_MAX
        for _ in range(self.iterations):
            new_board = RandomNeighbourBoard(board, self.fields_changed)
            new_score = self.classifier.classify(new_board)

            if new_score > score or math.exp((score - new_score) / t) > random.uniform(
                0, 1
            ):
                board = new_board
                score = new_score

                if score > best_score:
                    best_board = board
                    best_score = score

            t *= alpha

        return best_board
