from abc import ABC, abstractmethod
from algorithms.boards.board import Board


class Classifier(ABC):
    @abstractmethod
    def fit(self, data: list[tuple[Board, bool]]) -> float:
        pass

    @abstractmethod
    def classify(self, board: Board) -> float:
        pass

    @abstractmethod
    def save(self, filename: str) -> None:
        pass

    @abstractmethod
    def load(self, filename: str) -> None:
        pass
