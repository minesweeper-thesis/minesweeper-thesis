from algorithms.board import Board
from algorithms.random_board import RandomBoard
from is_solvable import is_solvable

class SolvableBoard(Board):
    def __init__(self, rows : int, columns : int, start_field : tuple[int,int], mine_count : int) -> None:
        while True:
            self = RandomBoard(rows,columns,start_field,mine_count)
            if is_solvable(self):
                break