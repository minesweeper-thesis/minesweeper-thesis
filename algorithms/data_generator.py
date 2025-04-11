import json
import random
from multiprocessing import Pool, Manager, cpu_count
from algorithms.random_board import RandomBoard
from algorithms.all_fields import all_fields
from algorithms.is_solvable import is_solvable
from multiprocessing import freeze_support


class DataGenerator:
    def __init__(self, rows: int, columns: int, mine_count: int) -> None:
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count
        self.filename = f"data/{rows},{columns},{mine_count}.json"
        self.fields = all_fields(rows, columns, (-2, -2))

    def _generate_batch(self, batch_size: int) -> list[dict]:
        data = []
        for i in range(batch_size):
            print(i)
            start_field = random.choice(self.fields)
            board = RandomBoard(self.rows, self.columns, start_field, self.mine_count)
            solvable = is_solvable(board)
            board_json = board.to_json()
            board_json["solvable"] = solvable
            data.append(board_json)
        return data

    def _worker(self, args) -> None:
        batch_count, batch_size, lock = args
        for i in range(batch_count):
            print(f"PID {random.getrandbits(16)} - batch {i}")
            data = self._generate_batch(batch_size)
            with lock:
                with open(self.filename, "a") as f:
                    for instance in data:
                        json.dump(instance, f)
                        f.write("\n")

    def generate(self, process_count: int, batch_count: int, batch_size: int):
        freeze_support()

        manager = Manager()
        lock = manager.Lock()
        args = [(batch_count, batch_size, lock) for _ in range(process_count)]

        with Pool(process_count) as pool:
            pool.map(self._worker, args)

if __name__ == "__main__":
    generator = DataGenerator(16, 30, 99)
    generator.generate(process_count=4, batch_count=10000, batch_size=10)

