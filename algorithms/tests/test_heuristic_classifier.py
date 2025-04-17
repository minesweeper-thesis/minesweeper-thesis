from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.heuristics.naive_heuristic import NaiveHeuristic
from algorithms.heuristics.particle_swarm_heuristic import ParticleSwarmHeuristic
from algorithms.boards.functions.is_solvable import is_solvable

classifier = LightGBMClassifier()
classifier.load("algorithms/tests/16,16,40.model")

for heuristic in (
    ParticleSwarmHeuristic(classifier, 16, 16, (4, 4), 40, 100, 10, True, True),
    ParticleSwarmHeuristic(classifier, 16, 16, (4, 4), 40, 100, 10, True, False),
    ParticleSwarmHeuristic(classifier, 16, 16, (4, 4), 40, 100, 10, False, True),
    ParticleSwarmHeuristic(classifier, 16, 16, (4, 4), 40, 100, 10, False, False),
    GeneticAlgorithmHeuristic(classifier, 16, 16, (4, 4), 40, 20, 50, 10, 0.05),
    NaiveHeuristic(classifier, 16, 16, (4, 4), 40, 1000),
):
    trues, falses = 0, 0

    for _ in range(100):
        board = heuristic.run()
        score = classifier.classify(board)
        solvable = is_solvable(board)
        # print(score,solvable)

        if solvable:
            trues += 1
        else:
            falses += 1

    print(trues / (trues + falses))
