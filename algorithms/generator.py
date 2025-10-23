from algorithms.boards.board import Board
from algorithms.boards.random_board import RandomBoard
from algorithms.checker.checker import Checker
from algorithms.classifiers.catboost_classifier import CatBoostClassifier
from algorithms.classifiers.classifier import Classifier
from algorithms.classifiers.gaussiannb_classifier import GaussianNBClassifier
from algorithms.classifiers.gradientboosting_classifier import (
    GradientBoostingClassifier,
)
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.classifiers.mlp_classifier import MLPClassifier
from algorithms.classifiers.xgboost_classifier import XGBoostClassifier
from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.heuristics.heuristic import Heuristic
from algorithms.heuristics.mcts_heuristic import MCTSHeuristic
from algorithms.heuristics.naive_heuristic import NaiveHeuristic
from algorithms.heuristics.no_heuristic import NoHeuristic
from algorithms.heuristics.particle_swarm_heuristic import ParticleSwarmHeuristic
from algorithms.heuristics.simulated_annealing_heuristic import (
    SimulatedAnnealingHeuristic,
)

_classifiers: dict[str, type[Classifier]] = {
    "lightgbm": LightGBMClassifier,
    "catboost": CatBoostClassifier,
    "gaussiannb": GaussianNBClassifier,
    "mlp": MLPClassifier,
    "xgboost": XGBoostClassifier,
    "gradientboosting": GradientBoostingClassifier,
}

_heuristics: dict[str, type[Heuristic]] = {
    "no": NoHeuristic,
    "naive": NaiveHeuristic,
    "GA": GeneticAlgorithmHeuristic,
    "MCTS": MCTSHeuristic,
    "PSO": ParticleSwarmHeuristic,
    "SA": SimulatedAnnealingHeuristic,
}


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
        classifier_iterations: int = -1,
    ) -> None:
        self.classifier = _classifiers[classifier]()

        iter_str = classifier_iterations if classifier_iterations > -1 else ""
        classifier_model_file = f"algorithms/models/{rows},{columns},{mine_count}_{classifier}{iter_str}.model"
        self.classifier.load(classifier_model_file)

        self.heuristic = _heuristics[heuristic](
            self.classifier, rows, columns, start_field, mine_count, *heuristic_args
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


class RandomGenerator:
    def __init__(
        self, rows: int, columns: int, mine_count: int, start_field: tuple[int, int]
    ):
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count
        self.start_field = start_field

    def generate(self):
        return RandomBoard(
            rows=self.rows,
            columns=self.columns,
            mine_count=self.mine_count,
            start_field=self.start_field,
        )
