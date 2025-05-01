from algorithms.boards.functions.moore import moore_neighborhood


class Grid:
    def print(self) -> None:
        for i in range(self.rows):
            print("", end="|")
            for j in range(self.columns):
                if self.flagged[i][j]:
                    print("X", end="|")
                elif self.revealed[i][j]:
                    print(self.grid[i][j], end="|")
                else:
                    print("-", end="|")
            print("")
        print("\n\n")

    def print_solved(self) -> None:
        for i in range(self.rows):
            print("", end="|")
            for j in range(self.columns):
                if self.grid[i][j] == -1:
                    print(" ", end="|")
                else:
                    print(self.grid[i][j], end="|")
            print("")
        print("\n\n")

    def check_win(self) -> bool:
        for row in range(self.rows):
            for col in range(self.columns):
                if self.grid[row][col] != -1 and not self.revealed[row][col]:
                    return False
        return True

    def handle_field_click(self, field: tuple[int, int]) -> None:
        x, y = field
        if self.revealed[x][y] or self.flagged[x][y]:
            return

        self.revealed[x][y] = True
        if self.grid[x][y] == 0:
            for r in range(max(0, x - 1), min(self.rows, x + 2)):
                for c in range(max(0, y - 1), min(self.columns, y + 2)):
                    if not self.revealed[r][c]:
                        self.handle_field_click((r, c))

    def convert_to_save(self) -> list[list[int]]:
        board = [[-1 for _ in range(self.columns)] for _ in range(self.rows)]
        for row in range(self.rows):
            for col in range(self.columns):
                if self.revealed[row][col]:
                    if self.grid[row][col] == -1:
                        board[row][col] = 9
                    else:
                        board[row][col] = self.grid[row][col]
                else:
                    board[row][col] = -1
        return board

    def __init__(
        self, rows: int, columns: int, mined_fields: list[tuple[int, int]]
    ) -> None:
        self.rows = rows
        self.columns = columns
        self.mined_fields = mined_fields
        self.grid = [[0 for _ in range(self.columns)] for _ in range(self.rows)]
        self.revealed = [[False for _ in range(self.columns)] for _ in range(self.rows)]
        self.flagged = [[False for _ in range(self.columns)] for _ in range(self.rows)]

        for i in range(len(self.mined_fields)):
            x, y = self.mined_fields[i]
            self.grid[x][y] = -1

            neighborhood = moore_neighborhood((x, y), self.rows, self.columns)
            for x_n, y_n in neighborhood:
                if self.grid[x_n][y_n] != -1:
                    self.grid[x_n][y_n] += 1
