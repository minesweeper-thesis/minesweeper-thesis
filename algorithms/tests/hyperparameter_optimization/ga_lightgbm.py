from algorithms.tests.hyperparameter_optimization.hyperparameter_optimizer import (
    HyperparameterOptimizer,
)
from skopt.space import Integer, Real

param_space = [
    Integer(1, 100, name="generations"),
    Integer(1, 100, name="population_size"),
    Integer(1, 100, name="parents_size"),
    Real(0.0, 1.0, prior="uniform", name="random_specimen_rate"),
]


def constraint_func(params):
    return params[2] > params[1]


rows, columns, mine_count, tries = 10, 10, 15, 100

optimizer = HyperparameterOptimizer(
    classifier="lightgbm",
    heuristic="GA",
    rows=rows,
    columns=columns,
    mine_count=mine_count,
    tries=tries,
    param_space=param_space,
    constraint=constraint_func,
)

optimizer.load(
    f"ga_hyperparameter_{rows},{columns},{mine_count},{tries}.hyperparameters"
)
optimizer.search(10)
optimizer.save(
    f"ga_hyperparameter_{rows},{columns},{mine_count},{tries}.hyperparameters"
)
print(optimizer.get_best())
