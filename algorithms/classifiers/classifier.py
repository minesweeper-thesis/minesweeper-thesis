from abc import ABC, abstractmethod
from algorithms.boards.board import Board
import joblib


class Classifier(ABC):
    def __init__(self):
        self.model = None

    @abstractmethod
    def fit(self, data: list[tuple[Board, bool]]) -> float:
        pass

    @abstractmethod
    def classify(self, board: Board) -> float:
        pass

    @abstractmethod
    def save(self, filename: str) -> None:
        pass

    @classmethod
    def load(cls, filename: str) -> "Classifier":
        instance = cls()
        instance.model = joblib.load(filename)
        return instance
