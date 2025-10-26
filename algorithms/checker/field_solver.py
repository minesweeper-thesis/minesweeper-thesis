from ortools.sat.python import cp_model


class FieldSolver:
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
