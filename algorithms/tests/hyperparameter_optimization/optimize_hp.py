import random
from pathlib import Path

from skopt.space import Integer, Real

from algorithms.tests.hyperparameter_optimization.hyperparameter_optimizer import (
    HyperparameterOptimizer,
)


TRIES = 20
ALL_ITERATIONS = 100

heuristics = ["GA", "PSO", "SA", "naive"]

param_spaces = {
    "GA": [
        Integer(1, 100, name="generations"),
        Integer(1, 100, name="population_size"),
        Integer(1, 100, name="parents_size"),
        Real(0.0, 1.0, prior="uniform", name="random_specimen_rate"),
    ],
    "PSO": [
        Integer(1, 100, name="iterations"),
        Integer(1, 100, name="particle_count"),
        Real(0.4, 0.9, prior="uniform", name="w_coefficient"),
        Real(1.0, 2.5, prior="uniform", name="c1_coefficient"),
        Real(1.0, 2.5, prior="uniform", name="c2_coefficient"),
    ],
    "SA": [
        Integer(1, 100, name="iterations"),
        Integer(1, 50, name="fields_changed"),
        Real(1.0, 1e2, prior="log-uniform", name="T_MAX"),
        Real(1e-1, 1, prior="log-uniform", name="T_MIN"),
    ],
    "naive": [
        Integer(1, 1000, name="tries"),
    ],
}


constraint_funcs = {
    "GA": lambda params: params[2] > params[1],
    "PSO": lambda _: False,
    "SA": lambda _: False,
    "naive": lambda _: False,
}


def constraint_func(params):
    global global_heuristic
    return constraint_funcs[global_heuristic](params)


hyperparameters = [  # to add: gradientboosting, mlp
    (10, 10, 15, "lightgbm", ("100", "800", "12800"), 100),
    (16, 16, 40, "lightgbm", ("100", "800", "12800"), 10),
    (16, 30, 99, "lightgbm", ("100", "200", "400"), 1),
    (10, 10, 15, "catboost", ("100", "800", "6400"), 100),
    (16, 16, 40, "catboost", ("100", "400", "3200"), 10),
    (16, 30, 99, "catboost", ("100", "400", "1600"), 1),
    (10, 10, 15, "xgboost", ("100", "800", "6400"), 100),
    (16, 16, 40, "xgboost", ("100", "800", "6400"), 10),
    (16, 30, 99, "xgboost", ("100", "400", "3200"), 1),
    (10, 10, 15, "gaussiannb", ("",), 100),
    (16, 16, 40, "gaussiannb", ("",), 10),
    (16, 30, 99, "gaussiannb", ("",), 1),
    (10, 10, 15, "mlp", ("(16,)", "(32, 16)", "(256, 16)"), 100),
    (16, 16, 40, "mlp", ("(16,)", "(256,)", "(64, 64)"), 10),
    (16, 30, 99, "mlp", ("(16,)", "(64,)", "(256,)"), 1),
]


def optimize(params):
    print(params)
    global global_heuristic

    (
        heuristic,
        rows,
        columns,
        mine_count,
        classifier,
        version,
        search_size,
    ) = params

    filename = f"algorithms/tests/hyperparameter_optimization/hyperparameters/{rows},{columns},{mine_count}_{classifier}{version}_{heuristic.lower()}_{TRIES}.hyperparameters"

    global_heuristic = heuristic

    optimizer = HyperparameterOptimizer(
        classifier=classifier,
        heuristic=heuristic,
        rows=rows,
        columns=columns,
        mine_count=mine_count,
        tries=TRIES,
        param_space=param_spaces[heuristic],
        constraint=constraint_func,
        version=version,
    )

    if Path(filename).exists():
        optimizer.load(filename)
    if optimizer.get_iterations_done() < ALL_ITERATIONS:
        optimizer.search(search_size)
        optimizer.save(filename)
    print(optimizer.get_best())


to_optimize = []

for heuristic in heuristics:
    for parameter_set in hyperparameters:
        rows, cols, mine_count, classifier, versions, search_size = parameter_set

        for version in versions:
            for _ in range(ALL_ITERATIONS // search_size):
                to_optimize.append(
                    (
                        heuristic,
                        rows,
                        cols,
                        mine_count,
                        classifier,
                        version,
                        search_size,
                    )
                )


random.shuffle(to_optimize)

for parameter_set in to_optimize:
    global_heuristic = parameter_set[0]
    optimize(parameter_set)
