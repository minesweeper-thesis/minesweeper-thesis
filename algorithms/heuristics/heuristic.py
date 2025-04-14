from abc import ABC, abstractmethod
from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class Heuristic(ABC):
    def __init__(
        self,
        classifier: Classifier,
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
    def run(self) -> Board:
        pass
