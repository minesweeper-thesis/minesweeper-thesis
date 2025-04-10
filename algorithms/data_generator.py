import json
import random
from algorithms.random_board import RandomBoard
from algorithms.all_fields import all_fields
from algorithms.is_solvable import is_solvable


class DataGenerator:
    def __init__(self, rows: int, columns: int, mine_count: int) -> None:
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count

        self.filename = (
            "data/" + str(rows) + "," + str(columns) + "," + str(mine_count) + ".json"
        )

    def generate(self, count: int) -> None:
        data = []

        fields = all_fields(self.rows, self.columns, (-2, -2))

        for i in range(count):
            print(i)

            start_field = fields[random.randint(0, len(fields) - 1)]
            board = RandomBoard(self.rows, self.columns, start_field, self.mine_count)
            solvable = is_solvable(board)
            board_json = board.to_json()
            board_json["solvable"] = solvable
            data.append(board_json)

        with open(self.filename, "a") as f:
            for instance in data:
                json.dump(instance, f)
                f.write("\n")


for j in range(50):
    print("\n", j, "\n")
    a = DataGenerator(16, 30, 99)
    a.generate(100)
