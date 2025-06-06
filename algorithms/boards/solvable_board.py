from algorithms.boards.board import Board
from algorithms.checker.checker import Checker
from algorithms.heuristics.heuristic import Heuristic


class SolvableBoard(Board):
    def __init__(
        self, heuristic: Heuristic
    ) -> None:
        checker = Checker(heuristic.rows,heuristic.columns,heuristic.start_field,heuristic.mine_count)
        while True:
            self = heuristic.run()
            
            if checker.is_solvable(self):
                break
