from algorithms.boards.board import Board
from algorithms.boards.random_board import RandomBoard
from algorithms.boards.functions.is_solvable import is_solvable
from algorithms.heuristics.heuristic import Heuristic


class SolvableBoard(Board):
    def __init__(
        self, heuristic: Heuristic
    ) -> None:
        while True:
            self = heuristic.run()
            if is_solvable(self):
                break
