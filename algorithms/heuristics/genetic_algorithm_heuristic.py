from algorithms.heuristics.heuristic import Heuristic
from algorithms.classifiers.classifier import Classifier
from algorithms.boards.board import Board
from algorithms.boards.ga_board import GABoard
import random


class GeneticAlgorithmHeuristic(Heuristic):
    def __init__(
        self,
        classifier: Classifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        
        generations: int,
        population_size: int,
        parents_size: int,
        random_specimens_rate: float,
    ) -> None:
        Heuristic.__init__(self, classifier, rows, columns, start_field, mine_count)
        self.generations = generations
        self.population_size = population_size
        self.parents_size = parents_size
        self.random_specimens_rate = random_specimens_rate

    def run(self) -> Board:
        boards = [
            GABoard(self.rows, self.columns, self.start_field, self.mine_count)
            for _ in range(self.population_size)
        ]

        population = [(self.classifier.classify(board), board) for board in boards]
        population.sort(key=lambda x: -x[0])

        for _ in range(self.generations):
            for i in range(self.parents_size, self.population_size):
                if random.uniform(0, 1) <= self.random_specimens_rate:
                    board = GABoard(
                        self.rows, self.columns, self.start_field, self.mine_count
                    )
                else:
                    _, board = population[i]
                    _, parent1 = population[random.randint(0, self.parents_size - 1)]
                    _, parent2 = population[random.randint(0, self.parents_size - 1)]

                    board.crossover(parent1, parent2)
                population[i] = (self.classifier.classify(board), board)

            population.sort(key=lambda x: -x[0])

        return population[0][1]
