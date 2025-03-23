from algorithms.board import Board
from algorithms.random_board import RandomBoard
from enum import Enum
import random
random.seed(10)

# W TRAKCIE IMPLEMENTACJI

class FieldState(Enum):
    MINED = -3
    NOT_MINED = -2
    POSSIBLE_MINE = -1
    NOT_REVEALED_NOT_NEIGHBOUR = 0
    NOT_REVEALED_NEIGHBOUR = 1
    REVEALED = 2

class SolvableBoard(Board):
    def __init__(self, rows : int, columns : int, start_field : tuple[int,int], mine_count : int) -> None:
        first_click = True
        running = True
        game_over_flag = False

        possible_moves = []
        empty_fields = []

        hint_cache_board = [[0 for _ in range(columns)] for _ in range(rows)]

        while running:
            if not first_click and len(possible_moves) > 0:
                while len(possible_moves) > 0:
                    grid.handle_field_click(possible_moves.pop(0))
            elif first_click:
                first_click = False
                self = RandomBoard(rows, columns, start_field, mine_count)
                grid = self.grid()

                grid.handle_field_click(start_field)

                #
                grid.print()
                #

                for i in range(rows):
                    for j in range(columns):
                        if grid.revealed[i][j] and grid.grid[i][j] == 0:
                            empty_fields.append((i,j))
                print("Empty fields: ", empty_fields)
            else:
                game_over_flag = True
            
            if grid.check_win():
                print("FOUND U")
                grid.print()
            else:
                not_mines = [[1 if hint_cache_board[i][j] == FieldState.NOT_MINED.value else 0 for j in range(self.columns)] for i in range(self.rows)]

                hint_cache_board = correct_hinted_board(grid, hint_cache_board)
                hint_cache_board = hint_safe_fields(hint_cache_board)

                for i in range(self.rows):
                    for j in range(self.columns):
                        if hint_cache_board[i][j] == FieldState.NOT_MINED.value and not grid.revealed[i][j]:
                            possible_moves.append((i, j))
                
                print("Possible moves: ", possible_moves)

a = SolvableBoard(10,10,(4,4),15)
