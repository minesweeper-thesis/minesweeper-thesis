from algorithms.boards.random_board import RandomBoard
from algorithms.boards.functions.all_fields import all_fields
from copy import deepcopy
import random


class PSOBoard(RandomBoard):
    """Board adjusted to the particle swarm optimization heuristic."""

    def __init__(
        self,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        w_coefficient: float = 0.729,
        c1_coefficient: float = 1.49445,
        c2_coefficient: float = 1.49445,
    ) -> None:
        """Initializes the board adjusted to the particle swarm optimization heuristic.

        Args:
            rows (int): number of rows of the board.
            columns (int): number of columns of the board.
            start_field (tuple[int, int]): coordinates of the first clicked field on the board.
            mine_count (int): number of mines on the board.
            w_coefficient (float, optional): w coefficient. Defaults to 0.729.
            c1_coefficient (float, optional): cognitive coefficient. Defaults to 1.49445.
            c2_coefficient (float, optional): social coefficient. Defaults to 1.49445.
        """
        RandomBoard.__init__(self, rows, columns, start_field, mine_count)
        self.best_position = deepcopy(self.mined_fields)
        self.best_score = 0.0
        self.velocity = [
            (
                random.uniform(-self.rows, self.rows),
                random.uniform(-self.columns, self.columns),
            )
            for _ in range(mine_count)
        ]
        self.w = w_coefficient
        self.c1 = c1_coefficient
        self.c2 = c2_coefficient

    def move(self, best_global_position: list[tuple[int, int]]) -> None:
        """Implements the move of the board through state space.

        Args:
            best_global_position (list[tuple[int, int]]): current best board configuration in the swarm.
        """
        p_diff = [
            (
                self.best_position[i][0] - self.mined_fields[i][0],
                self.best_position[i][1] - self.mined_fields[i][1],
            )
            for i in range(self.mine_count)
        ]
        g_diff = [
            (
                best_global_position[i][0] - self.mined_fields[i][0],
                best_global_position[i][1] - self.mined_fields[i][1],
            )
            for i in range(self.mine_count)
        ]

        self.velocity = [
            (
                self.w * self.velocity[i][0]
                + self.c1 * random.uniform(0, 1) * p_diff[i][0]
                + self.c2 * random.uniform(0, 1) * g_diff[i][0],
                self.w * self.velocity[i][1]
                + self.c1 * random.uniform(0, 1) * p_diff[i][1]
                + self.c2 * random.uniform(0, 1) * g_diff[i][1],
            )
            for i in range(self.mine_count)
        ]

        self.mined_fields = [
            (
                min(
                    self.rows - 1,
                    max(0, int(self.mined_fields[i][0] + self.velocity[i][0])),
                ),
                min(
                    self.columns - 1,
                    max(0, int(self.mined_fields[i][1] + self.velocity[i][1])),
                ),
            )
            for i in range(self.mine_count)
        ]

        fields = set(all_fields(self.rows, self.columns, self.start_field, []))
        to_change = []
        for i, field in enumerate(self.mined_fields):
            if field in fields:
                fields.remove(field)
            else:
                to_change.append(i)

        fields = list(fields)
        random.shuffle(fields)
        for i in range(len(to_change)):
            self.mined_fields[to_change[i]] = fields[i]
