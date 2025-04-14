from abc import ABC, abstractmethod
from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier

class Heuristic(ABC):
    def __init__(self, classifier : Classifier) -> None:
        self.classifier = classifier
        
    @abstractmethod
    def run(self) -> Board:
        pass