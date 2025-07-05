from algorithms.generator import Generator
from algorithms.boards.functions.all_fields import all_fields
from skopt import gp_minimize
from skopt.space import Integer, Real
import time
import random

TRIES = 100
fields = all_fields(16, 16, (-2, -2), [])
fields = [random.choice(fields) for _ in range(TRIES)]


def ga_wrapper(params):
    generations, population_size, parents_size, random_specimen_rate = params

    if parents_size > population_size:
        return 1e6

    start = time.time()

    for i in range(TRIES):
        Generator(
            "lightgbm",
            "GA",
            (generations, population_size, parents_size, random_specimen_rate),
            16,
            16,
            fields[i],
            40,
        ).generate()

    end = time.time()
    duration = end - start

    print(f"Params: {params} → Time: {duration:.4f}s")
    return duration


def no_wrapper():
    start = time.time()

    for i in range(TRIES):
        Generator(
            "lightgbm",
            "no",
            (),
            16,
            16,
            fields[i],
            40,
        ).generate()

    end = time.time()
    duration = end - start

    print(f"Time: {duration:.4f}s")
    return duration


def naive_wrapper():
    start = time.time()

    for i in range(TRIES):
        Generator(
            "lightgbm",
            "naive",
            (1000,),
            16,
            16,
            fields[i],
            40,
        ).generate()

    end = time.time()
    duration = end - start

    print(f"Time: {duration:.4f}s")
    return duration


"""
param_space = [
    Integer(1, 100, name="generations"),
    Integer(1, 100, name="population_size"),
    Integer(1, 100, name="parents_size"),
    Real(0.0, 1.0, prior="uniform", name="random_specimen_rate"),
]

res = gp_minimize(
    func=ga_wrapper,
    dimensions=param_space,
    n_calls=100,
    random_state=0,
)

print("Najlepszy czas:", res.fun)
print("Najlepsze parametry:", res.x)"""

ga_wrapper((10, 100, 20, 0.05))
no_wrapper()
naive_wrapper()
