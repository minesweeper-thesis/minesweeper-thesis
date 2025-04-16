from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.heuristics.naive_heuristic import NaiveHeuristic
from algorithms.boards.functions.is_solvable import is_solvable

classifier = LightGBMClassifier()
classifier.load('algorithms/tests/10,10,15.model')

#heuristic = GeneticAlgorithmHeuristic(10,10,(4,4),15,classifier,100,50,10,0.05)
heuristic = NaiveHeuristic(classifier,10,10,(4,4),15,5000)

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