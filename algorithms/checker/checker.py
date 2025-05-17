from algorithms.boards.board import Board
from algorithms.boards.grid import Grid
from ortools.sat.python import cp_model
from enum import Enum
import numpy as np


class Checker:
    def __init__(
        self, rows: int, columns: int, start_field: tuple[int, int], mine_count: int
    ) -> None:
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count

    def is_solvable(self, board: Board) -> bool:
        first_click = True

        possible_moves = []
        empty_fields = []

        hint_cache_board = [
            [_FieldState.NOT_REVEALED_NOT_NEIGHBOUR.value for _ in range(self.columns)]
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
                            if hint_cache_board[i][j] == _FieldState.NOT_MINED.value
                            else 0
                        )
                        for j in range(self.columns)
                    ]
                    for i in range(self.rows)
                ]
                hint_generator = _HintGenerator(grid, not_mines, self.mine_count)

                hint_cache_board = hint_generator.correct_hinted_board(hint_cache_board)
                hint_cache_board = hint_generator.hint_safe_fields(hint_cache_board)

                for i in range(self.rows):
                    for j in range(self.columns):
                        if (
                            hint_cache_board[i][j] == _FieldState.NOT_MINED.value
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
                                hint_cache_board[i][j] == _FieldState.NOT_MINED.value
                                and not grid.revealed[i][j]
                            ):
                                possible_moves.append((i, j))

                    if not possible_moves:
                        return False


class _FieldState(Enum):
    MINED = -3
    NOT_MINED = -2
    POSSIBLE_MINE = -1
    NOT_REVEALED_NOT_NEIGHBOUR = 0
    NOT_REVEALED_NEIGHBOUR = 1
    REVEALED = 2


class _FieldSolver:
    def __init__(
        self, fields: list[list[int]], not_mines: list[list[int]], mine_count: int
    ) -> None:
        self.fields = fields
        self.not_mines = not_mines
        self.rows = len(not_mines)
        self.columns = len(not_mines[0])
        self.mine_count = mine_count

    def field_is_mined(self, x: int, y: int) -> list[list[bool]] | list:
        model = cp_model.CpModel()

        potential_mines = [
            [model.NewBoolVar(f"mine_{i}_{j}") for j in range(self.columns)]
            for i in range(self.rows)
        ]
        potential_board = [
            [model.NewIntVar(-1, 9, f"board_{i}_{j}") for j in range(self.columns)]
            for i in range(self.rows)
        ]

        model.Add(potential_mines[x][y] == 0)

        for i in range(self.rows):
            for j in range(self.columns):
                if self.fields[i][j] != -1:
                    model.Add(potential_mines[i][j] == 0)
                    model.Add(potential_board[i][j] == self.fields[i][j])

        model.Add(
            sum(
                potential_mines[i][j]
                for i in range(self.rows)
                for j in range(self.columns)
            )
            == self.mine_count
        )

        for i in range(self.rows):
            for j in range(self.columns):
                if self.not_mines[i][j] == 1 and (i != x and j != y):
                    model.Add(potential_mines[i][j] == 0)

        for i in range(self.rows):
            for j in range(self.columns):
                neighbors = []
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if (
                            (di != 0 or dj != 0)
                            and 0 <= i + di < self.rows
                            and 0 <= j + dj < self.columns
                        ):
                            neighbors.append(potential_mines[i + di][j + dj])
                model.Add(potential_board[i][j] == 9).OnlyEnforceIf(
                    potential_mines[i][j]
                )
                model.Add(potential_board[i][j] == sum(neighbors)).OnlyEnforceIf(
                    potential_mines[i][j].Not()
                )

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return [
                [
                    solver.BooleanValue(potential_mines[i][j])
                    for j in range(self.columns)
                ]
                for i in range(self.rows)
            ]
        else:
            return []

    def field_is_safe(self, x: int, y: int) -> list[list[bool]] | list:
        model = cp_model.CpModel()

        potential_mines = [
            [model.NewBoolVar(f"mine_{i}_{j}") for j in range(self.columns)]
            for i in range(self.rows)
        ]
        potential_board = [
            [model.NewIntVar(-1, 9, f"board_{i}_{j}") for j in range(self.columns)]
            for i in range(self.rows)
        ]

        model.Add(potential_mines[x][y] == 1)

        for i in range(self.rows):
            for j in range(self.columns):
                if self.fields[i][j] != -1:
                    model.Add(potential_mines[i][j] == 0)
                    model.Add(potential_board[i][j] == self.fields[i][j])

        model.Add(
            sum(
                potential_mines[i][j]
                for i in range(self.rows)
                for j in range(self.columns)
            )
            == self.mine_count
        )

        for i in range(self.rows):
            for j in range(self.columns):
                if self.not_mines[i][j] == 1:
                    model.Add(potential_mines[i][j] == 0)

        for i in range(self.rows):
            for j in range(self.columns):
                neighbors = []
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if (
                            (di != 0 or dj != 0)
                            and 0 <= i + di < self.rows
                            and 0 <= j + dj < self.columns
                        ):
                            neighbors.append(potential_mines[i + di][j + dj])
                model.Add(potential_board[i][j] == 9).OnlyEnforceIf(
                    potential_mines[i][j]
                )
                model.Add(potential_board[i][j] == sum(neighbors)).OnlyEnforceIf(
                    potential_mines[i][j].Not()
                )

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return [
                [
                    solver.BooleanValue(potential_mines[i][j])
                    for j in range(self.columns)
                ]
                for i in range(self.rows)
            ]
        else:
            return []


class _HintGenerator:
    def __init__(self, grid: Grid, not_mines: list[list[int]], mine_count: int) -> None:
        self.grid = grid
        self.rows = grid.rows
        self.columns = grid.columns
        self.not_mines = not_mines
        self.mine_count = mine_count

    def correct_hinted_board(
        self, hint_cache_board: list[list[int]]
    ) -> list[list[int]]:
        board = self.grid.convert_to_save()
        for i in range(self.rows):
            for j in range(self.columns):
                if hint_cache_board[i][j] not in (
                    _FieldState.POSSIBLE_MINE.value,
                    _FieldState.NOT_REVEALED_NOT_NEIGHBOUR.value,
                    _FieldState.NOT_REVEALED_NEIGHBOUR.value,
                ):
                    continue

                if self.grid.flagged[i][j]:
                    hint_cache_board[i][j] = _FieldState.POSSIBLE_MINE.value
                    continue

                for r in range(max(0, i - 1), min(self.rows, i + 2)):
                    for c in range(max(0, j - 1), min(self.columns, j + 2)):
                        if (board[r][c] != -1 or self.grid.flagged[r][c]) and (
                            r != i or c != j
                        ):
                            hint_cache_board[i][
                                j
                            ] = _FieldState.NOT_REVEALED_NEIGHBOUR.value

                if board[i][j] != -1:
                    hint_cache_board[i][j] = _FieldState.REVEALED.value

        return hint_cache_board

    def hint_safe_fields(self, hint_cache_board: list[list[int]]) -> list[list[int]]:
        fields = self.grid.convert_to_save()
        field_solver = _FieldSolver(fields, self.not_mines, self.mine_count)

        temp_board = np.zeros((self.rows, self.columns))

        for i in range(self.rows):
            for j in range(self.columns):
                if (
                    hint_cache_board[i][j] != _FieldState.NOT_REVEALED_NEIGHBOUR.value
                    or temp_board[i, j] == True
                ):
                    continue

                solutions = field_solver.field_is_safe(i, j)

                is_unsat = len(solutions) == 0

                if is_unsat:
                    hint_cache_board[i][j] = _FieldState.NOT_MINED.value
                else:
                    temp_board = np.logical_or(temp_board, np.array(solutions))

        return hint_cache_board

    def hint_mined_fields(self, hint_cache_board: list[list[int]]) -> list[list[int]]:
        fields = self.grid.convert_to_save()
        field_solver = _FieldSolver(fields, self.not_mines, self.mine_count)
        temp_board = np.zeros((self.rows, self.columns))

        for i in range(self.rows):
            for j in range(self.columns):
                if (
                    hint_cache_board[i][j] != _FieldState.NOT_REVEALED_NEIGHBOUR.value
                    or temp_board[i, j] == True
                ):
                    continue

                solutions = field_solver.field_is_mined(i, j)

                is_unsat = len(solutions) == 0

                if is_unsat:
                    hint_cache_board[i][j] = _FieldState.MINED.value
                    self.grid.flagged[i][j] = True
                else:
                    temp_board = np.logical_or(temp_board, np.array(solutions))

        return hint_cache_board
