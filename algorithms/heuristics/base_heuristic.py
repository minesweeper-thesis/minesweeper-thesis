from abc import ABC, abstractmethod
from algorithms.boards.base_board import BaseBoard
from algorithms.classifiers.base_classifier import BaseClassifier


class BaseHeuristic(ABC):
    def __init__(
        self,
        classifier: BaseClassifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
    ) -> None:
        self.classifier = classifier
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count

    @abstractmethod
    def run(self) -> BaseBoard:
        pass
