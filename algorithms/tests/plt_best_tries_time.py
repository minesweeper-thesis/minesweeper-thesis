from pathlib import Path
import time as tm
import random
import matplotlib.pyplot as plt
import statistics as stats

from skopt.space import Integer, Real

from algorithms.tests.hyperparameter_optimization.hyperparameter_optimizer import (
    HyperparameterOptimizer,
)
from algorithms.boards.functions.dispersion import dispersion
from algorithms.generator_joblib import Generator
from algorithms.boards.functions.all_fields import all_fields


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


TRIES_NOW = 100
efficient_frontier = {}

for rows, cols, mines in ((10, 10, 15), (16, 16, 40), (16, 30, 99)):
    efficient_frontier[(rows, cols, mines)] = []


to_optimize = []

for heuristic in heuristics:
    for parameter_set in hyperparameters:
        (rows, cols, mine_count), rests = parameter_set
        fields = all_fields(rows, cols, (-2, -2), [])
        fields = [random.choice(fields) for _ in range(TRIES_NOW)]
        best_time = 1e6

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

                if time < best_time:
                    best_time = time
                    best_classifier = classifier
                    best_version = version
                    best_params = params

        print(
            heuristic,
            rows,
            cols,
            mine_count,
            best_time / 20,
            best_classifier + best_version,
            best_params,
        )

        boards = []
        tries = []
        times = []
        for i in range(TRIES_NOW):
            start = tm.time()

            generated_board, tries_count = Generator(
                best_classifier,
                heuristic,
                best_params,
                rows,
                cols,
                fields[i],
                mine_count,
                best_version,
            ).generate()
            boards.append(generated_board)

            end = tm.time()

            tries.append(tries_count)
            times.append(end - start)

        efficient_frontier[(rows, cols, mine_count)].append(
            (heuristic, stats.mean(times), dispersion(boards))
        )

        weights = [1 / len(times)] * len(times)
        plt.hist(times, bins=20, weights=weights)

        plt.xlabel("Generation Time (s)")
        plt.ylabel("Frequency")
        plt.title(
            f"Histogram of Generation Time\n{heuristic}, {best_classifier}{best_version}, {rows}x{cols} board, {mine_count} mines\navg = {stats.mean(times):.3f}, stdev = {stats.stdev(times):.3f}"
        )
        plt.grid(True)

        plt.tight_layout()
        plt.savefig(
            f"algorithms/tests/plots/{heuristic}_{rows},{cols},{mine_count}_hist_times.png"
        )

        plt.clf()

        weights = [1 / len(tries)] * len(tries)
        bins = range(min(tries), max(tries) + 2)

        plt.hist(tries, bins=bins, weights=weights, rwidth=0.8)

        plt.xlabel("Generation Tries")
        plt.ylabel("Frequency")
        plt.title(
            f"Histogram of Generation Tries\n{heuristic}, {best_classifier}{best_version}, {rows}x{cols} board, {mine_count} mines\navg = {stats.mean(tries):.3f}, stdev = {stats.stdev(tries):.3f}"
        )
        bin_centers = [(b + bins[i + 1]) / 2 for i, b in enumerate(bins[:-1])]

        plt.xticks(bin_centers, range(min(tries), max(tries) + 1))
        plt.grid(True)

        plt.tight_layout()
        plt.savefig(
            f"algorithms/tests/plots/{heuristic}_{rows},{cols},{mine_count}_hist_tries.png"
        )

        plt.clf()


for rows, cols, mine_count in [(10, 10, 15), (16, 16, 40), (16, 30, 99)]:
    fields = all_fields(rows, cols, (-2, -2), [])
    fields = [random.choice(fields) for _ in range(TRIES_NOW)]

    tries = []
    times = []
    boards = []

    for i in range(TRIES_NOW):
        start = tm.time()

        generated_board, tries_count = Generator(
            None,
            "no",
            (),
            rows,
            cols,
            fields[i],
            mine_count,
            "",
        ).generate()
        boards.append(generated_board)

        end = tm.time()

        tries.append(tries_count)
        times.append(end - start)

    print(dispersion(boards))

    efficient_frontier[(rows, cols, mine_count)].append(
        ("no", stats.mean(times), dispersion(boards))
    )

    weights = [1 / len(times)] * len(times)
    plt.hist(times, bins=20, weights=weights)

    plt.xlabel("Generation Time (s)")
    plt.ylabel("Frequency")
    plt.title(
        f"Histogram of Generation Time\nno heuristic, {rows}x{cols} board, {mine_count} mines\navg = {stats.mean(times):.3f}, stdev = {stats.stdev(times):.3f}"
    )
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(f"algorithms/tests/plots/no_{rows},{cols},{mine_count}_hist_times.png")

    plt.clf()

    weights = [1 / len(tries)] * len(tries)
    bins = range(min(tries), max(tries) + 2)

    plt.hist(tries, bins=bins, weights=weights, rwidth=0.8)

    plt.xlabel("Generation Tries")
    plt.ylabel("Frequency")
    plt.title(
        f"Histogram of Generation Tries\nno heuristic, {rows}x{cols} board, {mine_count} mines\navg = {stats.mean(tries):.3f}, stdev = {stats.stdev(tries):.3f}"
    )
    bin_centers = [(b + bins[i + 1]) / 2 for i, b in enumerate(bins[:-1])]

    plt.xticks(bin_centers, range(min(tries), max(tries) + 1))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(f"algorithms/tests/plots/no_{rows},{cols},{mine_count}_hist_tries.png")

    plt.clf()


for (rows, cols, mine_count), data in efficient_frontier.items():
    names, generation_times, dispersions = zip(*data)

    plt.figure(figsize=(8, 6))
    plt.scatter(generation_times, dispersions, color="blue")

    for name, x, y in zip(names, generation_times, dispersions):
        plt.text(x, y, name, fontsize=10, ha="right", va="bottom")

    plt.xlabel("Generation Time (s)")
    plt.ylabel("Dispersion (0-1)")
    plt.title(
        f"Heuristic Generation Time vs Dispersion\n{rows}x{cols} board, {mine_count} mines"
    )
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"algorithms/tests/plots/{rows},{cols},{mine_count}_dispersion.png")

    plt.clf()
