import math
from pathlib import Path

from skopt.space import Integer, Real

from algorithms.tests.hyperparameter_optimization.hyperparameter_optimizer import (
    HyperparameterOptimizer,
)


TRIES = 20

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
        Real(0.4, 0.9, prior="uniform", name="random_specimen_rate"),
        Real(1.0, 2.5, prior="uniform", name="random_specimen_rate"),
        Real(1.0, 2.5, prior="uniform", name="random_specimen_rate"),
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


hyperparameters = [
    (
        (10, 10, 15),
        (
            ("lightgbm", ("100", "800", "12800")),
            ("catboost", ("100", "800", "6400")),
            ("xgboost", ("100", "800", "6400")),
            ("gaussiannb", ("",)),
            ("mlp", ("(16,)", "(32, 16)", "(256, 16)")),
        ),
    ),
    (
        (16, 16, 40),
        (
            ("lightgbm", ("100", "800", "12800")),
            ("catboost", ("100", "400", "3200")),
            ("xgboost", ("100", "800", "6400")),
            ("gaussiannb", ("",)),
            ("mlp", ("(16,)", "(256,)", "(64, 64)")),
        ),
    ),
    (
        (16, 30, 99),
        (
            ("lightgbm", ("100", "200", "400")),
            ("catboost", ("100", "400", "1600")),
            ("xgboost", ("100", "400", "3200")),
            ("gaussiannb", ("",)),
            ("mlp", ("(16,)", "(64,)", "(256,)")),
        ),
    ),
]


def optimize(params):
    global global_heuristic

    (
        heuristic,
        rows,
        columns,
        mine_count,
        classifier,
        version,
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

    return optimizer


to_optimize = []

for heuristic in heuristics:
    for parameter_set in hyperparameters:
        (rows, cols, mine_count), rests = parameter_set

        values = []
        for rest in rests:
            classifier, versions = rest

            for version in versions:
                global_heuristic = heuristic

                optimizer = optimize(
                    (
                        heuristic,
                        rows,
                        cols,
                        mine_count,
                        classifier,
                        version,
                    )
                )

                params, time = optimizer.get_best()

                value = optimizer.get_values()

                value = [value[0]] + [min(value[:i]) for i in range(1, len(value))]
                value = [v / TRIES if v < 1e6 else math.nan for v in value]

                values.append((value, classifier + version))

        import matplotlib.pyplot as plt

        plt.figure()
        for value in values:
            plt.plot(value[0], label=value[1])

        plt.xlabel("Hyperparameter optimization iteration")
        plt.ylabel("Average generation time (s)")
        plt.title(f"Best time for {heuristic}, {rows}x{cols} board, {mine_count} mines")
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.savefig(
            f"algorithms/tests/plots/{heuristic}_{rows},{cols},{mine_count}.png"
        )

        plt.clf()
