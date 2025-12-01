import random
import time
from typing import Callable

import joblib
from skopt import Optimizer

from algorithms.boards.functions.all_fields import all_fields
from algorithms.generator_joblib import Generator


class HyperparameterOptimizer:
    def __init__(
        self,
        classifier: str,
        heuristic: str,
        rows: int,
        columns: int,
        mine_count: int,
        tries: int,
        param_space: list,
        constraint: Callable[[tuple], bool],
        version: str,
    ) -> None:
        self.classifier = classifier
        self.heuristic = heuristic
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count
        self.tries = tries
        self.version = version
        self.fields = all_fields(rows, columns, (-2, -2), [])
        self.fields = [random.choice(self.fields) for _ in range(tries)]
        self.constraint = constraint
        self.optimizer = Optimizer(
            dimensions=param_space,
            base_estimator="GP",
            acq_func="EI",
            random_state=0,
        )

    def search(self, iterations: int):
        for _ in range(iterations):
            next_params = self.optimizer.ask()
            self.optimizer.tell(next_params, self._heuristic_wrapper(next_params))

    def get_best(self) -> tuple:
        best_idx = self.optimizer.yi.index(min(self.optimizer.yi))
        return self.optimizer.Xi[best_idx], self.optimizer.yi[best_idx]

    def _heuristic_wrapper(self, params: tuple) -> float:
        if self.constraint(params):
            return 1e6

        start = time.time()

        for i in range(self.tries):
            Generator(
                self.classifier,
                self.heuristic,
                params,
                self.rows,
                self.columns,
                self.fields[i],
                self.mine_count,
                self.version,
            ).generate()

        end = time.time()
        duration = end - start

        print(f"Params: {params} → Time: {duration:.4f}s")
        return duration

    def save(self, filename: str) -> None:
        state = {
            "classifier": self.classifier,
            "heuristic": self.heuristic,
            "rows": self.rows,
            "columns": self.columns,
            "mine_count": self.mine_count,
            "tries": self.tries,
            "constraint": self.constraint,
            "fields": self.fields,
            "optimizer": self.optimizer,
        }
        open(filename, "w").close()
        joblib.dump(state, filename)

    def load(self, filename: str) -> None:
        state = joblib.load(filename)
        self.classifier = state["classifier"]
        self.heuristic = state["heuristic"]
        self.rows = state["rows"]
        self.columns = state["columns"]
        self.mine_count = state["mine_count"]
        self.tries = state["tries"]
        self.constraint = state["constraint"]
        self.fields = state["fields"]
        self.optimizer = state["optimizer"]

    def get_iterations_done(self) -> int:
        return len(self.optimizer.Xi)
