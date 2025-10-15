import lightgbm as lgb
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score
from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class LightGBMClassifier(Classifier):
    """Classifier based on lightgbm."""

    def __init__(self, num_boost_round: int = 100) -> None:
        """Initializes classifier parameters.

        Args:
            num_boost_round (int, optional): number of boosting rounds. Defaults to 100.
        """
        self.num_boost_round = num_boost_round

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

        train_data = lgb.Dataset(X_train, label=y_train)

        self.model = lgb.train(
            {
                "objective": "binary",
                "metric": "binary_logloss",
                "verbosity": -1,
                "is_unbalance": True,
            },
            train_data,
            num_boost_round=self.num_boost_round,
        )

        preds = self.model.predict(X_test)
        preds_binary = (preds > 0.5).astype(int)
        return balanced_accuracy_score(y_test, preds_binary)

    def classify(self, board: Board) -> float:
        """Classifies the board.

        Args:
            board (Board): board to classify.

        Returns:
            float: probability that the board is deterministically solvable.
        """
        return float(self.model.predict(board.model_input().reshape(1, -1))[0])

    def save(self, filename: str) -> None:
        """Saves the classifier model.

        Args:
            filename (str): path to the model.
        """
        open(filename, "w").close()
        joblib.dump(self.model, filename)

    def load(self, filename: str) -> None:
        """Loads the classifier model.

        Args:
            filename (str): path to the model.
        """
        self.model = joblib.load(filename)
