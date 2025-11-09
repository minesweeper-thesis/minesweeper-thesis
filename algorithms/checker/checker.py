from algorithms.boards.board import BaseBoard
from algorithms.checker.field_state import FieldState
from algorithms.checker.hint_generator import HintGenerator


class Checker:
    def __init__(
        self, rows: int, columns: int, start_field: tuple[int, int], mine_count: int
    ) -> None:
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count

    def is_solvable(self, board: BaseBoard) -> bool:
        first_click = True

        possible_moves = []
        empty_fields = []

        hint_cache_board = [
            [FieldState.NOT_REVEALED_NOT_NEIGHBOUR.value for _ in range(self.columns)]
            for _ in range(self.rows)
        ]

        while True:
            if not first_click and len(possible_moves) > 0:
                while len(possible_moves) > 0:
                    grid.handle_field_click(possible_moves.pop(0))
            elif first_click:
                first_click = False

                grid = board.grid()

                grid.handle_field_click(self.start_field)

                for i in range(self.rows):
                    for j in range(self.columns):
                        if grid.revealed[i][j] and grid.grid[i][j] == 0:
                            empty_fields.append((i, j))
            else:
                return False

            if grid.check_win():
                return True
            else:
                not_mines = [
                    [
                        (
                            1
                            if hint_cache_board[i][j] == FieldState.NOT_MINED.value
                            else 0
                        )
                        for j in range(self.columns)
                    ]
                    for i in range(self.rows)
                ]
                hint_generator = HintGenerator(grid, not_mines)

                hint_cache_board = hint_generator.correct_hinted_board(hint_cache_board)
                hint_cache_board = hint_generator.hint_safe_fields(hint_cache_board)

                for i in range(self.rows):
                    for j in range(self.columns):
                        if (
                            hint_cache_board[i][j] == FieldState.NOT_MINED.value
                            and not grid.revealed[i][j]
                        ):
                            possible_moves.append((i, j))

                if not possible_moves:
                    hint_cache_board = hint_generator.hint_mined_fields(
                        hint_cache_board
                    )
                    hint_cache_board = hint_generator.correct_hinted_board(
                        hint_cache_board
                    )
                    hint_cache_board = hint_generator.hint_safe_fields(hint_cache_board)

                    for i in range(self.rows):
                        for j in range(self.columns):
                            if (
                                hint_cache_board[i][j] == FieldState.NOT_MINED.value
                                and not grid.revealed[i][j]
                            ):
                                possible_moves.append((i, j))

                    if not possible_moves:
                        return False
