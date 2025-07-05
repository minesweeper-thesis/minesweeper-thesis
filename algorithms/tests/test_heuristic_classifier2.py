from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.heuristics.naive_heuristic import NaiveHeuristic
from algorithms.heuristics.no_heuristic import NoHeuristic
from algorithms.heuristics.mcts_heuristic import MCTSHeuristic
from algorithms.heuristics.particle_swarm_heuristic import ParticleSwarmHeuristic
from algorithms.boards.functions.all_fields import all_fields
import random


'''
GeneticAlgorithmHeuristic(
                    classifier,
                    rows,
                    columns,
                    fields[i],
                    mines,
                    int(total_boards_no / 50),
                    50,
                    10,
                    0.05,
                ),
                ParticleSwarmHeuristic(
                    classifier,
                    rows,
                    columns,
                    fields[i],
                    mines,
                    int(total_boards_no / 25),
                    25,
                ),'''

rows, columns, mines = 16, 30, 99
tries = 10
classifier = LightGBMClassifier()
classifier.load(
    "algorithms/models/" + str(rows) + "," + str(columns) + "," + str(mines) + "_lightgbm.model"
)
fields = all_fields(rows, columns, (-2, -2), [])
fields = [random.choice(fields) for _ in range(tries)]

for total_boards_no in (
    50,
    100,
    250,
    500,
    1000,
    2500,
    5000,
    10000,
    25000,
    50000,
    100000
):
    score = [0.0, 0.0, 0.0, 0.0, 0.0]

    print(total_boards_no, end="\t")
    for i in range(tries):
        for id, heuristic in enumerate(
            (
                NaiveHeuristic(
                    classifier, rows, columns, fields[i], mines, total_boards_no
                ),
                GeneticAlgorithmHeuristic(classifier, rows, columns, fields[i], mines, int(total_boards_no/50), 50, 10, 0.05),
                ParticleSwarmHeuristic(classifier, rows, columns, fields[i], mines, int(total_boards_no/50), 50)
                #MCTSHeuristic(classifier, rows, columns, fields[i], mines, int(total_boards_no), 15),
                #MCTSHeuristic(classifier, rows, columns, fields[i], mines, max(int(total_boards_no/20),1), 15, 20),
                #MCTSHeuristic(classifier, rows, columns, fields[i], mines, max(int(total_boards_no/20/3),1), 5, 20),
                #MCTSHeuristic(classifier, rows, columns, fields[i], mines, max(int(total_boards_no/20/15),1), 1, 20),
                #NoHeuristic(rows, columns, fields[i], mines),
            )
        ):
            board = heuristic.run()
            score[id] += classifier.classify(board) / tries
    for element in score:
        print(element, end="\t")
    print("")
