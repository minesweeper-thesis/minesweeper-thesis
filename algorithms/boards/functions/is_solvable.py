from algorithms.boards.board import Board
from algorithms.boards.functions.field_state import FieldState
from algorithms.boards.grid import Grid
import numpy as np
from ortools.sat.python import cp_model


def field_is_mined(fields, not_mines, x, y, rows, cols, mines_count):
    model = cp_model.CpModel()

    potential_mines = [
        [model.NewBoolVar(f"mine_{i}_{j}") for j in range(cols)] for i in range(rows)
    ]
    potential_board = [
        [model.NewIntVar(-1, 9, f"board_{i}_{j}") for j in range(cols)]
        for i in range(rows)
    ]

    model.Add(potential_mines[x][y] == 0)

    for i in range(rows):
        for j in range(cols):
            if fields[i][j] != -1:
                model.Add(potential_mines[i][j] == 0)
                model.Add(potential_board[i][j] == fields[i][j])

    model.Add(
        sum(potential_mines[i][j] for i in range(rows) for j in range(cols))
        == mines_count
    )

    for i in range(rows):
        for j in range(cols):
            if not_mines[i][j] == 1 and (i != x and j != y):
                model.Add(potential_mines[i][j] == 0)

    for i in range(rows):
        for j in range(cols):
            neighbors = []
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if (
                        (di != 0 or dj != 0)
                        and 0 <= i + di < rows
                        and 0 <= j + dj < cols
                    ):
                        neighbors.append(potential_mines[i + di][j + dj])
            model.Add(potential_board[i][j] == 9).OnlyEnforceIf(potential_mines[i][j])
            model.Add(potential_board[i][j] == sum(neighbors)).OnlyEnforceIf(
                potential_mines[i][j].Not()
            )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return [
            [solver.BooleanValue(potential_mines[i][j]) for j in range(cols)]
            for i in range(rows)
        ]
    else:
        return []


def field_is_safe(fields, not_mines, x, y, rows, cols, mines_count):
    model = cp_model.CpModel()

    potential_mines = [
        [model.NewBoolVar(f"mine_{i}_{j}") for j in range(cols)] for i in range(rows)
    ]
    potential_board = [
        [model.NewIntVar(-1, 9, f"board_{i}_{j}") for j in range(cols)]
        for i in range(rows)
    ]

    model.Add(potential_mines[x][y] == 1)

    for i in range(rows):
        for j in range(cols):
            if fields[i][j] != -1:
                model.Add(potential_mines[i][j] == 0)
                model.Add(potential_board[i][j] == fields[i][j])

    model.Add(
        sum(potential_mines[i][j] for i in range(rows) for j in range(cols))
        == mines_count
    )

    for i in range(rows):
        for j in range(cols):
            if not_mines[i][j] == 1:
                model.Add(potential_mines[i][j] == 0)

    for i in range(rows):
        for j in range(cols):
            neighbors = []
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if (
                        (di != 0 or dj != 0)
                        and 0 <= i + di < rows
                        and 0 <= j + dj < cols
                    ):
                        neighbors.append(potential_mines[i + di][j + dj])
            model.Add(potential_board[i][j] == 9).OnlyEnforceIf(potential_mines[i][j])
            model.Add(potential_board[i][j] == sum(neighbors)).OnlyEnforceIf(
                potential_mines[i][j].Not()
            )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return [
            [solver.BooleanValue(potential_mines[i][j]) for j in range(cols)]
            for i in range(rows)
        ]
    else:
        return []


def hint_mined_fields(
    hint_cache_board: list[list[int]], grid: Grid, not_mines: list[list[int]]
) -> list[list[int]]:
    fields, rows, cols, mines_count = (
        grid.convert_to_save(),
        grid.rows,
        grid.columns,
        len(grid.mined_fields),
    )
    temp_board = np.zeros((rows, cols))

    for i in range(rows):
        for j in range(cols):
            if hint_cache_board[i][j] != 1 or temp_board[i, j] == True:
                continue

            solutions = field_is_mined(fields, not_mines, i, j, rows, cols, mines_count)

            is_unsat = len(solutions) == 0

            if is_unsat:
                hint_cache_board[i][j] = -3
                grid.flagged[i][j] = True
            else:
                temp_board = np.logical_or(temp_board, np.array(solutions))

    return hint_cache_board


def hint_safe_fields(
    hint_cache_board: list[list[int]], grid: Grid, not_mines: list[list[int]]
) -> list[list[int]]:
    fields, rows, cols, mines_count = (
        grid.convert_to_save(),
        grid.rows,
        grid.columns,
        len(grid.mined_fields),
    )
    temp_board = np.zeros((rows, cols))

    for i in range(rows):
        for j in range(cols):
            if (
                hint_cache_board[i][j] != FieldState.NOT_REVEALED_NEIGHBOUR.value
                or temp_board[i, j] == True
            ):
                continue

            solutions = field_is_safe(fields, not_mines, i, j, rows, cols, mines_count)

            is_unsat = len(solutions) == 0

            if is_unsat:
                hint_cache_board[i][j] = FieldState.NOT_MINED.value
            else:
                temp_board = np.logical_or(temp_board, np.array(solutions))

    return hint_cache_board


def correct_hinted_board(
    grid: Grid, hint_cache_board: list[list[int]]
) -> list[list[int]]:
    board = grid.convert_to_save()
    ROWS, COLS = grid.rows, grid.columns
    for i in range(ROWS):
        for j in range(COLS):
            if hint_cache_board[i][j] not in (
                FieldState.POSSIBLE_MINE.value,
                FieldState.NOT_REVEALED_NOT_NEIGHBOUR.value,
                FieldState.NOT_REVEALED_NEIGHBOUR.value,
            ):
                continue

            if grid.flagged[i][j]:
                hint_cache_board[i][j] = FieldState.POSSIBLE_MINE.value
                continue

            for r in range(max(0, i - 1), min(ROWS, i + 2)):
                for c in range(max(0, j - 1), min(COLS, j + 2)):
                    if (board[r][c] != -1 or grid.flagged[r][c]) and (r != i or c != j):
                        hint_cache_board[i][j] = FieldState.NOT_REVEALED_NEIGHBOUR.value

            if board[i][j] != -1:
                hint_cache_board[i][j] = FieldState.REVEALED.value

    return hint_cache_board


def correct_hinted_board(
    grid: Grid, hint_cache_board: list[list[int]]
) -> list[list[int]]:
    board = grid.convert_to_save()
    ROWS, COLS = grid.rows, grid.columns
    for i in range(ROWS):
        for j in range(COLS):
            if hint_cache_board[i][j] not in (
                FieldState.POSSIBLE_MINE.value,
                FieldState.NOT_REVEALED_NOT_NEIGHBOUR.value,
                FieldState.NOT_REVEALED_NEIGHBOUR.value,
            ):
                continue

            if grid.flagged[i][j]:
                hint_cache_board[i][j] = FieldState.POSSIBLE_MINE.value
                continue

            for r in range(max(0, i - 1), min(ROWS, i + 2)):
                for c in range(max(0, j - 1), min(COLS, j + 2)):
                    if (board[r][c] != -1 or grid.flagged[r][c]) and (r != i or c != j):
                        hint_cache_board[i][j] = FieldState.NOT_REVEALED_NEIGHBOUR.value

            if board[i][j] != -1:
                hint_cache_board[i][j] = FieldState.REVEALED.value

    return hint_cache_board


def is_solvable(board: Board) -> bool:
    rows, columns, start_field = board.rows, board.columns, board.start_field

    first_click = True

    possible_moves = []
    empty_fields = []

    hint_cache_board = [[0 for _ in range(columns)] for _ in range(rows)]

    while True:
        if not first_click and len(possible_moves) > 0:
            while len(possible_moves) > 0:
                grid.handle_field_click(possible_moves.pop(0))
        elif first_click:
            first_click = False

            grid = board.grid()

            grid.handle_field_click(start_field)

            for i in range(rows):
                for j in range(columns):
                    if grid.revealed[i][j] and grid.grid[i][j] == 0:
                        empty_fields.append((i, j))
        else:
            return False

        if grid.check_win():
            return True
        else:
            not_mines = [
                [
                    1 if hint_cache_board[i][j] == FieldState.NOT_MINED.value else 0
                    for j in range(columns)
                ]
                for i in range(rows)
            ]
            hint_cache_board = correct_hinted_board(grid, hint_cache_board)
            hint_cache_board = hint_safe_fields(hint_cache_board, grid, not_mines)

            for i in range(rows):
                for j in range(columns):
                    if (
                        hint_cache_board[i][j] == FieldState.NOT_MINED.value
                        and not grid.revealed[i][j]
                    ):
                        possible_moves.append((i, j))

            if not possible_moves:
                hint_cache_board = hint_mined_fields(hint_cache_board, grid, not_mines)
                hint_cache_board = correct_hinted_board(grid, hint_cache_board)
                hint_cache_board = hint_safe_fields(hint_cache_board, grid, not_mines)

                for i in range(rows):
                    for j in range(columns):
                        if hint_cache_board[i][j] == -2 and not grid.revealed[i][j]:
                            possible_moves.append((i, j))

                if not possible_moves:
                    return False
