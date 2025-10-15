from abc import ABC, abstractmethod
from algorithms.boards.board import Board


class Classifier(ABC):
    """Base class for classifiers."""

    @abstractmethod
    def fit(self, data: list[tuple[Board, bool]]) -> float:
        """Trains the classifier on provided data.

        Args:
            data (list[tuple[Board, bool]]): list of pairs (board, deterministic or not?).

        Returns:
            float: balanced accuracy on testing subset.
        """
        pass

    @abstractmethod
    def classify(self, board: Board) -> float:
        """Classifies the board.

        Args:
            board (Board): board to classify.

        Returns:
            float: probability that the board is deterministically solvable.
        """
        pass

    @abstractmethod
    def save(self, filename: str) -> None:
        """Saves the classifier model.

        Args:
            filename (str): path to the model.
        """
        pass

    @abstractmethod
    def load(self, filename: str) -> None:
        """Loads the classifier model.

        Args:
            filename (str): path to the model.
        """
        pass
