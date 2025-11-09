from algorithms.heuristics.heuristic import BaseHeuristic
from algorithms.boards.base_board import BaseBoard
from algorithms.boards.pso_board import PSOBoard
from algorithms.classifiers.base_classifier import BaseClassifier
from copy import deepcopy


class ParticleSwarmHeuristic(BaseHeuristic):
    def __init__(
        self,
        classifier: BaseClassifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        iterations: int,
        particle_count: int,
        w_coefficient: float = 0.729,
        c1_coefficient: float = 1.49445,
        c2_coefficient: float = 1.49445,
    ) -> None:
        BaseHeuristic.__init__(self, classifier, rows, columns, start_field, mine_count)
        self.iterations = iterations
        self.w = w_coefficient
        self.c1 = c1_coefficient
        self.c2 = c2_coefficient
        self.particle_count = particle_count

    def run(self) -> BaseBoard:
        best_global_position = None
        best_score = 0
        particles = [
            PSOBoard(
                self.rows,
                self.columns,
                self.start_field,
                self.mine_count,
                self.w,
                self.c1,
                self.c2,
            )
            for _ in range(self.particle_count)
        ]

        for board in particles:
            score = self.classifier.classify(board)
            if score > best_score:
                best_global_position = deepcopy(board.mined_fields)
                self.best_score = score

        for _ in range(self.iterations):
            for board in particles:
                board.move(best_global_position)

                current_particle_score = self.classifier.classify(board)

                if current_particle_score > board.best_score:
                    board.best_position = deepcopy(board.mined_fields)
                    board.best_score = current_particle_score

                    if current_particle_score > best_score:
                        best_global_position = deepcopy(board.mined_fields)
                        best_score = current_particle_score

        return BaseBoard(
            self.rows,
            self.columns,
            self.start_field,
            self.mine_count,
            best_global_position,
        )
