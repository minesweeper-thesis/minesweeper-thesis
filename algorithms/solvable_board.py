from algorithms.board import Board
from algorithms.random_board import RandomBoard

# W TRAKCIE IMPLEMENTACJI

class SolvableBoard(Board):
    def __init__(self, rows : int, columns : int, start_field : tuple[int,int], mine_count : int) -> None:
        first_click = True
        running = True
        game_over_flag = False

        revealed = [[False for _ in range(columns)] for _ in range(rows)]
        flagged = [[False for _ in range(columns)] for _ in range(rows)]
        possible_moves = []
        empty_fields = []

        hint_cache_board = [[0 for _ in range(columns)] for _ in range(rows)]

        sum_of_hints = 0
        sum_of_three_depth = 0

        while running:
            if not first_click and len(possible_moves) > 0:
                while len(possible_moves) > 0:
                    x, y = possible_moves.pop(0)
                    handle_field_click(grid, revealed, start_field)
            elif first_click:
                first_click = False
                grid = RandomBoard(rows, columns, start_field, mine_count).board()
                print(grid)

                handle_field_click(grid, revealed, start_field)

                for i in range(rows):
                    for j in range(columns):
                        if revealed[i][j] and grid[i][j] == 0:
                            empty_fields.append((i,j))
                print("Empty fields: ", empty_fields)
            else:
                game_over_flag = True