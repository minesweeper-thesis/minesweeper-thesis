from abc import ABC, abstractmethod
from algorithms.boards.board import Board

class Classifier:
    @abstractmethod
    def fit(self, data : list[tuple[Board, bool]]) -> float:
        pass

    @abstractmethod
    def classify(self, board : Board) -> bool:
        pass

    @abstractmethod
    def save(self) -> None:
        pass

    @abstractmethod
    def load(self, source : str) -> None:
        pass