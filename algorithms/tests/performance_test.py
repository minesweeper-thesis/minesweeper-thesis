from algorithms.generator import Generator
from algorithms.boards.functions.all_fields import all_fields
import time
import random

TRIES = 5
fields = all_fields(16, 30, (-2, -2), [])
fields = [random.choice(fields) for _ in range(TRIES)]


def ga_wrapper(params):
    generations, population_size, parents_size, random_specimen_rate = params

    if parents_size > population_size:
        return 1e6

    start = time.process_time()

    for i in range(TRIES):
        Generator(
            "lightgbm",
            "GA",
            (generations, population_size, parents_size, random_specimen_rate),
            16,
            30,
            fields[i],
            99,
            "algorithms/models/16,30,99_lightgbm400.model",
        ).generate()

    end = time.process_time()
    duration = end - start

    print(f"Params: {params} → Time: {duration:.4f}s")
    return duration


def no_wrapper():
    start = time.process_time()

    for i in range(TRIES):
        Generator(
            "lightgbm",
            "no",
            (),
            16,
            30,
            fields[i],
            99,
            "algorithms/models/16,30,99_lightgbm400.model",
        ).generate()

    end = time.process_time()
    duration = end - start

    print(f"Time: {duration:.4f}s")
    return duration


def naive_wrapper():
    start = time.process_time()

    for i in range(TRIES):
        Generator(
            "lightgbm",
            "naive",
            (1000,),
            16,
            30,
            fields[i],
            99,
            "algorithms/models/16,30,99_lightgbm400.model",
        ).generate()

    end = time.process_time()
    duration = end - start

    print(f"Time: {duration:.4f}s")
    return duration


for _ in range(10):
    ga_wrapper((100, 20, 1, 0.0))
    ga_wrapper((10, 50, 10, 0.02))
    no_wrapper()

    print("\n")
