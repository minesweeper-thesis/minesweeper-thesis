import random
from pathlib import Path

from skopt.space import Integer

from algorithms.tests.hyperparameter_optimization.hyperparameter_optimizer import (
    HyperparameterOptimizer,
)

TRIES = 20
ALL_ITERATIONS = 100

param_space = [
    Integer(1, 1000, name="tries"),
]


def constraint_func(params):
    return False


def optimize(params):
    print(params)
    rows, columns, mine_count, classifier, classifier_iterations, search_size = params

    iter_str = classifier_iterations if classifier_iterations > -1 else ""
    filename = f"algorithms/tests/hyperparameter_optimization/hyperparameters/{rows},{columns},{mine_count}_{classifier}{iter_str}_naive_{TRIES}.hyperparameters"

    optimizer = HyperparameterOptimizer(
        classifier=classifier,
        heuristic="naive",
        rows=rows,
        columns=columns,
        mine_count=mine_count,
        tries=TRIES,
        param_space=param_space,
        constraint=constraint_func,
        classifier_iterations=classifier_iterations,
    )

    if Path(filename).exists():
        optimizer.load(filename)
    if optimizer.get_iterations_done() < ALL_ITERATIONS:
        optimizer.search(search_size)
        optimizer.save(filename)
    print(optimizer.get_best())


hyperparameters = [
    (10, 10, 15, "lightgbm", (100, 800, 12800), 100),
    (16, 16, 40, "lightgbm", (100, 800, 12800), 10),
    (16, 30, 99, "lightgbm", (100, 200, 400), 1),
    (10, 10, 15, "catboost", (100, 800, 6400), 100),
    (16, 16, 40, "catboost", (100, 400, 3200), 10),
    (16, 30, 99, "catboost", (100, 400, 1600), 1),
    (10, 10, 15, "xgboost", (100, 800, 6400), 100),
    (16, 16, 40, "xgboost", (100, 800, 6400), 10),
    (16, 30, 99, "xgboost", (100, 400, 3200), 1),
    (10, 10, 15, "gaussiannb", (-1,), 100),
    (16, 16, 40, "gaussiannb", (-1,), 10),
    (16, 30, 99, "gaussiannb", (-1,), 1),
]


to_optimize = []


for parameter_set in hyperparameters:
    rows, cols, mine_count, classifier, classifier_iterations, search_size = (
        parameter_set
    )

    for iterations in classifier_iterations:
        for _ in range(ALL_ITERATIONS // search_size):
            to_optimize.append(
                (rows, cols, mine_count, classifier, iterations, search_size)
            )


random.shuffle(to_optimize)

for parameter_set in to_optimize:
    optimize(parameter_set)
