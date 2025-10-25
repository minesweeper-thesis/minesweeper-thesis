from algorithms.boards.grid import Grid
from algorithms.checker.field_state import FieldState
from algorithms.checker.field_solver import FieldSolver
import numpy as np


class HintGenerator:
    def __init__(self, grid: Grid, not_mines: list[list[int]]) -> None:
        self.grid = grid
        self.rows = grid.rows
        self.columns = grid.columns
        self.not_mines = not_mines
        self.mine_count = len(grid.mined_fields)

    @staticmethod
    def get_safe_fields_no_cache(grid: Grid) -> list[tuple[int, int]]:
        possible_moves = []

        not_mines = [
            [(int(grid.revealed[i][j])) for j in range(grid.columns)]
            for i in range(grid.rows)
        ]

        hint_generator = HintGenerator(grid, not_mines)

        hint_board = [
            [FieldState.NOT_REVEALED_NOT_NEIGHBOUR.value for _ in range(grid.columns)]
            for _ in range(grid.rows)
        ]

        hint_board = hint_generator.correct_hinted_board(hint_board)
        hint_board = hint_generator.hint_safe_fields(hint_board)

        for i in range(grid.rows):
            for j in range(grid.columns):
                if (
                    hint_board[i][j] == FieldState.NOT_MINED.value
                    and not grid.revealed[i][j]
                ):
                    possible_moves.append((i, j))

        if not possible_moves:
            hint_board = hint_generator.hint_mined_fields(hint_board)
            hint_board = hint_generator.correct_hinted_board(hint_board)
            hint_board = hint_generator.hint_safe_fields(hint_board)

            for i in range(grid.rows):
                for j in range(grid.columns):
                    if (
                        hint_board[i][j] == FieldState.NOT_MINED.value
                        and not grid.revealed[i][j]
                    ):
                        possible_moves.append((i, j))

        return possible_moves

    def correct_hinted_board(
        self, hint_cache_board: list[list[int]]
    ) -> list[list[int]]:
        board = self.grid.convert_to_save()
        for i in range(self.rows):
            for j in range(self.columns):
                if hint_cache_board[i][j] not in (
                    FieldState.POSSIBLE_MINE.value,
                    FieldState.NOT_REVEALED_NOT_NEIGHBOUR.value,
                    FieldState.NOT_REVEALED_NEIGHBOUR.value,
                ):
                    continue

                if self.grid.flagged[i][j]:
                    hint_cache_board[i][j] = FieldState.POSSIBLE_MINE.value
                    continue

                for r in range(max(0, i - 1), min(self.rows, i + 2)):
                    for c in range(max(0, j - 1), min(self.columns, j + 2)):
                        if (board[r][c] != -1 or self.grid.flagged[r][c]) and (
                            r != i or c != j
                        ):
                            hint_cache_board[i][
                                j
                            ] = FieldState.NOT_REVEALED_NEIGHBOUR.value

                if board[i][j] != -1:
                    hint_cache_board[i][j] = FieldState.REVEALED.value

        return hint_cache_board

    def hint_safe_fields(self, hint_cache_board: list[list[int]]) -> list[list[int]]:
        fields = self.grid.convert_to_save()
        field_solver = FieldSolver(fields, self.not_mines, self.mine_count)

        temp_board = np.zeros((self.rows, self.columns))

        for i in range(self.rows):
            for j in range(self.columns):
                if (
                    hint_cache_board[i][j] != FieldState.NOT_REVEALED_NEIGHBOUR.value
                    or temp_board[i, j] == True
                ):
                    continue

                solutions = field_solver.field_is_safe(i, j)

                is_unsat = len(solutions) == 0

                if is_unsat:
                    hint_cache_board[i][j] = FieldState.NOT_MINED.value
                else:
                    hint_cache_board[i][j] = FieldState.POSSIBLE_MINE.value  #
                    temp_board = np.logical_or(temp_board, np.array(solutions))

        return hint_cache_board

    def hint_mined_fields(self, hint_cache_board: list[list[int]]) -> list[list[int]]:
        fields = self.grid.convert_to_save()
        field_solver = FieldSolver(fields, self.not_mines, self.mine_count)
        temp_board = np.zeros((self.rows, self.columns))

        for i in range(self.rows):
            for j in range(self.columns):
                if (
                    hint_cache_board[i][j] != FieldState.NOT_REVEALED_NEIGHBOUR.value
                    or temp_board[i, j] == True
                ):
                    continue

                solutions = field_solver.field_is_mined(i, j)

                is_unsat = len(solutions) == 0

                if is_unsat:
                    hint_cache_board[i][j] = FieldState.MINED.value
                    self.grid.flagged[i][j] = True
                else:
                    temp_board = np.logical_or(temp_board, np.array(solutions))

        return hint_cache_board
