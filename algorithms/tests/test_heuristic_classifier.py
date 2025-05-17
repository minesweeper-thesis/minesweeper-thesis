from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.heuristics.naive_heuristic import NaiveHeuristic
from algorithms.heuristics.no_heuristic import NoHeuristic
from algorithms.heuristics.particle_swarm_heuristic import ParticleSwarmHeuristic
from algorithms.checker.checker import Checker

classifier = LightGBMClassifier()
classifier.load("algorithms/tests/16,30,99.model")
checker = Checker(16,30,(7,14),99)

for heuristic in (
    ParticleSwarmHeuristic(classifier, 16, 30, (7, 14), 99, 200, 25),
    GeneticAlgorithmHeuristic(classifier, 16, 30, (7, 14), 99, 100, 50, 10, 0.05),
    NaiveHeuristic(classifier, 16, 30, (7, 14), 99, 5000),
):
    trues, falses = 0, 0

    for _ in range(50):
        board = heuristic.run()
        score = classifier.classify(board)
        solvable = checker.is_solvable(board)
        print(score,solvable)

        if solvable:
            trues += 1
        else:
            falses += 1

    print(trues / (trues + falses))