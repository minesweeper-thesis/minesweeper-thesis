from abc import ABC, abstractmethod
from algorithms.boards.base_board import BaseBoard
import joblib


class BaseClassifier(ABC):
    def __init__(self):
        self.model = None

    @abstractmethod
    def fit(self, data: list[tuple[BaseBoard, bool]]) -> float:
        pass

    @abstractmethod
    def classify(self, board: BaseBoard) -> float:
        pass

    @abstractmethod
    def save(self, filename: str) -> None:
        pass

    @classmethod
    def load(cls, filename: str) -> "BaseClassifier":
        instance = cls()
        instance.model = joblib.load(filename)
        return instance
