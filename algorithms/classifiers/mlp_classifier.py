from sklearn.neural_network import MLPClassifier as SklearnMLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score
import numpy as np
import joblib
from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class MLPClassifier(Classifier):
    """Classifier based on a simple neural network."""

    def __init__(self, hidden_layer_sizes=(100,), max_iter=200) -> None:
        """Initializes classifier parameters.

        Args:
            hidden_layer_sizes (tuple, optional): list with hidden layers sizes. Defaults to (100,).
            max_iter (int, optional): max iterations. Defaults to 200.
        """
        self.hidden_layer_sizes = hidden_layer_sizes
        self.max_iter = max_iter

    def fit(self, data: list[tuple[Board, bool]]) -> float:
        """Trains the classifier on provided data.

        Args:
            data (list[tuple[Board, bool]]): list of pairs (board, deterministic or not?).

        Returns:
            float: balanced accuracy on testing subset.
        """
        X = np.array([board.model_input().reshape(-1) for board, _ in data])
        y = np.array([int(label) for _, label in data])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y
        )

        self.model = SklearnMLPClassifier(
            hidden_layer_sizes=self.hidden_layer_sizes, max_iter=self.max_iter
        )
        self.model.fit(X_train, y_train)

        preds = self.model.predict(X_test)
        return balanced_accuracy_score(y_test, preds)

    def classify(self, board: Board) -> float:
        """Classifies the board.

        Args:
            board (Board): board to classify.

        Returns:
            float: probability that the board is deterministically solvable.
        """
        return float(self.model.predict_proba(board.model_input().reshape(1, -1))[0][1])

    def save(self, filename: str) -> None:
        """Saves the classifier model.

        Args:
            filename (str): path to the model.
        """
        joblib.dump(self.model, filename)

    def load(self, filename: str) -> None:
        """Loads the classifier model.

        Args:
            filename (str): path to the model.
        """
        self.model = joblib.load(filename)
