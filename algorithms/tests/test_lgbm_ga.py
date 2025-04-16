from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.boards.functions.is_solvable import is_solvable

classifier = LightGBMClassifier()
classifier.load('algorithms/tests/16,30,99.model')

heuristic = GeneticAlgorithmHeuristic(16,30,(4,4),99,classifier,100,50,10,0.05)

trues, falses = 0, 0

for _ in range(100):
    board = heuristic.run()
    score = classifier.classify(board)
    solvable = is_solvable(board)
    print(score,solvable)

    if solvable:
        trues += 1
    else:
        falses += 1

print(trues/(trues+falses))