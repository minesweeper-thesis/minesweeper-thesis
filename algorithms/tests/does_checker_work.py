from algorithms.data.data_loader import DataLoader
from algorithms.checker.checker import Checker


data = DataLoader(16,30,99).load()
for board, solvable in data:
    checker = Checker(16,30,board.start_field,99)
    print(solvable == checker.is_solvable(board))