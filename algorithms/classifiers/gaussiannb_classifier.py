import joblib
from sklearn.naive_bayes import GaussianNB as SklearnGaussianNB

from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class GaussianNBClassifier(Classifier):
    def __init__(self) -> None:
        self.model = None

    def fit(self, data: list[tuple[Board, bool]]) -> float:
        if self.model is None:
            raise RuntimeError("Model already loaded.")

        import numpy as np
        from sklearn.metrics import balanced_accuracy_score
        from sklearn.model_selection import train_test_split

        self.model = SklearnGaussianNB()
        X = np.array([board.model_input().reshape(-1) for board, _ in data])
        y = np.array([int(label) for _, label in data])
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y
        )
        self.model.fit(X_train, y_train)
        preds = self.model.predict(X_test)
        return balanced_accuracy_score(y_test, preds)

    def classify(self, board: Board) -> float:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        return float(self.model.predict_proba(board.model_input().reshape(1, -1))[0][1])

    def save(self, filename: str) -> None:
        joblib.dump(self.model, filename)

    @classmethod
    def load(cls, filename: str) -> "GaussianNBClassifier":
        instance = cls()
        instance.model = joblib.load(filename)
        return instance
