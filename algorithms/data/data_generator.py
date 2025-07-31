import json
import random
import threading
from multiprocessing import Pool, Manager, cpu_count
from algorithms.boards.random_board import RandomBoard
from algorithms.boards.functions.all_fields import all_fields
from algorithms.checker.checker import Checker
from multiprocessing import freeze_support


class DataGenerator:
    def __init__(self, rows: int, columns: int, mine_count: int) -> None:
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count
        self.filename = f"data/{rows},{columns},{mine_count}.json"
        self.fields = all_fields(rows, columns, (-2, -2), [])

    def _generate_batch(self, batch_size: int) -> list[dict]:
        data = []
        for i in range(batch_size):
            print(i)
            start_field = random.choice(self.fields)
            board = RandomBoard(self.rows, self.columns, start_field, self.mine_count)
            checker = Checker(self.rows, self.columns, start_field, self.mine_count)
            solvable = checker.is_solvable(board)
            board_json = board.to_json()
            board_json["solvable"] = solvable
            data.append(board_json)
        return data

    def _worker(self, args: list[tuple[int, int, threading.Lock, int]]) -> None:
        batch_count, batch_size, lock, number = args
        for i in range(batch_count):
            print(f"PID {number} - batch {i}")
            data = self._generate_batch(batch_size)
            with lock:
                with open(self.filename, "a") as f:
                    for instance in data:
                        json.dump(instance, f)
                        f.write("\n")

    def generate(self, process_count: int, batch_count: int, batch_size: int) -> None:
        freeze_support()

        manager = Manager()
        lock = manager.Lock()
        args = [(batch_count, batch_size, lock, i) for i in range(process_count)]

        with Pool(process_count) as pool:
            pool.map(self._worker, args)


if __name__ == "__main__":
    generator = DataGenerator(16, 16, 40)
    generator.generate(process_count=cpu_count(), batch_count=256, batch_size=14)
