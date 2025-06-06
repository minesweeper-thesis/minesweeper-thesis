from algorithms.checker.checker import Checker

from algorithms.boards.board import Board

from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.classifiers.catboost_classifier import CatBoostClassifier
from algorithms.classifiers.gaussiannb_classifier import GaussianNBClassifier
from algorithms.classifiers.gradientboosting_classifier import (
    GradientBoostingClassifier,
)
from algorithms.classifiers.mlp_classifier import MLPClassifier
from algorithms.classifiers.xgboost_classifier import XGBoostClassifier

from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.heuristics.mcts_heuristic import MCTSHeuristic
from algorithms.heuristics.naive_heuristic import NaiveHeuristic
from algorithms.heuristics.no_heuristic import NoHeuristic
from algorithms.heuristics.particle_swarm_heuristic import ParticleSwarmHeuristic
from algorithms.heuristics.simulated_annealing_heuristic import (
    SimulatedAnnealingHeuristic,
)


class Generator:
    def __init__(
        self,
        classifier: str,
        heuristic: str,
        heuristic_args: tuple,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
    ) -> None:
        match classifier:
            case "lightgbm":
                self.classifier = LightGBMClassifier()
            case "catboost":
                self.classifier = CatBoostClassifier()
            case "gaussian":
                self.classifier = GaussianNBClassifier()
            case "mlp":
                self.classifier = MLPClassifier()
            case "xgboost":
                self.classifier = XGBoostClassifier()
            case "gradientboosting":
                self.classifier = GradientBoostingClassifier()

        classifier_model_file = (
            "algorithms/models/"
            + str(rows)
            + ","
            + str(columns)
            + ","
            + str(mine_count)
            + "_"
            + classifier
            + ".model"
        )
        self.classifier.load(classifier_model_file)

        match heuristic:
            case "no":
                self.heuristic = NoHeuristic(rows, columns, start_field, mine_count)
            case "naive":
                self.heuristic = NaiveHeuristic(
                    self.classifier,
                    rows,
                    columns,
                    start_field,
                    mine_count,
                    heuristic_args[0],
                )
            case "GA":
                self.heuristic = GeneticAlgorithmHeuristic(
                    self.classifier,
                    rows,
                    columns,
                    start_field,
                    mine_count,
                    heuristic_args[0],
                    heuristic_args[1],
                    heuristic_args[2],
                    heuristic_args[3],
                )
            case "MCTS":
                self.heuristic = MCTSHeuristic(
                    self.classifier,
                    rows,
                    columns,
                    start_field,
                    mine_count,
                    heuristic_args[0],
                    heuristic_args[1],
                    heuristic_args[2],
                    heuristic_args[3],
                )
            case "PSO":
                self.heuristic = ParticleSwarmHeuristic(
                    self.classifier,
                    rows,
                    columns,
                    start_field,
                    mine_count,
                    heuristic_args[0],
                    heuristic_args[1],
                    heuristic_args[2],
                    heuristic_args[3],
                    heuristic_args[4],
                )
            case "SA":
                self.heuristic = SimulatedAnnealingHeuristic(
                    self.classifier,
                    rows,
                    columns,
                    start_field,
                    mine_count,
                    heuristic_args[0],
                    heuristic_args[1],
                    heuristic_args[2],
                    heuristic_args[3],
                )

    def generate(self) -> Board:
        checker = Checker(
            self.heuristic.rows,
            self.heuristic.columns,
            self.heuristic.start_field,
            self.heuristic.mine_count,
        )
        while True:
            board = self.heuristic.run()

            if checker.is_solvable(board):
                return board

