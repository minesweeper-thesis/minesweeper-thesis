from algorithms.tests.hyperparameter_optimization.hyperparameter_optimizer import (
    HyperparameterOptimizer,
)
from skopt.space import Integer, Real
from pathlib import Path

param_space = [
    Integer(1, 100, name="generations"),
    Integer(1, 100, name="population_size"),
    Integer(1, 100, name="parents_size"),
    Real(0.0, 1.0, prior="uniform", name="random_specimen_rate"),
]


def constraint_func(params):
    return params[2] > params[1]


rows, columns, mine_count, tries, classifier = (
    16,
    30,
    99,
    20,
    "gaussiannb",
)

"""for classifier_iterations in (3200,):

    optimizer = HyperparameterOptimizer(
        classifier="lightgbm",
        heuristic="GA",
        rows=rows,
        columns=columns,
        mine_count=mine_count,
        tries=tries,
        param_space=param_space,
        constraint=constraint_func,
        classifier_model_file=f"algorithms/models/{rows},{columns},{mine_count}_{classifier}{classifier_iterations}.model",
    )

    filename = f"algorithms/tests/hyperparameter_optimization/hyperparameters/{rows},{columns},{mine_count}_{classifier}{classifier_iterations}_ga_{tries}.hyperparameters"
    if Path(filename).exists():
        optimizer.load(filename)
    optimizer.search(100)
    optimizer.save(filename)
    print(optimizer.get_best())
"""


optimizer = HyperparameterOptimizer(
    classifier="lightgbm",
    heuristic="GA",
    rows=rows,
    columns=columns,
    mine_count=mine_count,
    tries=tries,
    param_space=param_space,
    constraint=constraint_func,
    classifier_model_file=f"algorithms/models/{rows},{columns},{mine_count}_{classifier}.model",
)

for _ in range(1):
    filename = f"algorithms/tests/hyperparameter_optimization/hyperparameters/{rows},{columns},{mine_count}_{classifier}_ga_{tries}.hyperparameters"
    if Path(filename).exists():
        optimizer.load(filename)
    optimizer.search(10)
    optimizer.save(filename)
    print(optimizer.get_best())
