import joblib
from catboost import CatBoostClassifier as CBC

from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class CatBoostClassifier(Classifier):
    def __init__(self, num_boost_round: int = 100) -> None:
        self.num_boost_round = num_boost_round
        self.model = None

    def fit(self, data: list[tuple[Board, bool]]) -> float:
        if self.model is None:
            raise RuntimeError("Model already loaded.")

        import numpy as np
        from sklearn.metrics import balanced_accuracy_score
        from sklearn.model_selection import train_test_split

        X = np.array([board.model_input().reshape(-1) for board, _ in data])
        y = np.array([int(label) for _, label in data])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y
        )

        self.model = CBC(
            iterations=self.num_boost_round,
            loss_function="Logloss",
            class_weights=[1.0, sum(y == 0) / sum(y == 1)],
        )
        self.model.fit(X_train, y_train, verbose=0)

        preds = self.model.predict(X_test)
        return balanced_accuracy_score(y_test, preds)

    def classify(self, board: Board) -> float:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        return float(self.model.predict_proba(board.model_input().reshape(1, -1))[0, 1])

    def save(self, filename: str) -> None:
        joblib.dump(self.model, filename)

    @classmethod
    def load(cls, filename: str) -> "CatBoostClassifier":
        instance = cls()
        instance.model = joblib.load(filename)
        return instance
