from algorithms.boards.base_board import BaseBoard
from algorithms.checker.checker import Checker
from algorithms.classifiers.catboost_classifier import CatBoostClassifier
from algorithms.classifiers.base_classifier import BaseClassifier
from algorithms.classifiers.gaussiannb_classifier import GaussianNBClassifier
from algorithms.classifiers.gradientboosting_classifier import (
    GradientBoostingClassifier,
)
from algorithms.classifiers.lightgbm_classifier import LightGBMClassifier
from algorithms.classifiers.mlp_classifier import MLPClassifier
from algorithms.classifiers.xgboost_classifier import XGBoostClassifier
from algorithms.heuristics.genetic_algorithm_heuristic import GeneticAlgorithmHeuristic
from algorithms.heuristics.base_heuristic import BaseHeuristic
from algorithms.heuristics.mcts_heuristic import MCTSHeuristic
from algorithms.heuristics.naive_heuristic import NaiveHeuristic
from algorithms.heuristics.no_heuristic import NoHeuristic
from algorithms.heuristics.particle_swarm_heuristic import ParticleSwarmHeuristic
from algorithms.heuristics.simulated_annealing_heuristic import (
    SimulatedAnnealingHeuristic,
)

_classifiers: dict[str, type[BaseClassifier]] = {
    "lightgbm": LightGBMClassifier,
    "catboost": CatBoostClassifier,
    "gaussiannb": GaussianNBClassifier,
    "mlp": MLPClassifier,
    "xgboost": XGBoostClassifier,
    "gradientboosting": GradientBoostingClassifier,
}

_heuristics: dict[str, type[BaseHeuristic]] = {
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
        iter_str = classifier_iterations if classifier_iterations > -1 else ""
        classifier_model_file = f"algorithms/models/{rows},{columns},{mine_count}_{classifier}{iter_str}.model"
        self.classifier = _classifiers[classifier].load(classifier_model_file)

        self.heuristic = _heuristics[heuristic](
            self.classifier, rows, columns, start_field, mine_count, *heuristic_args
        )

    def generate(self) -> BaseBoard:
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
