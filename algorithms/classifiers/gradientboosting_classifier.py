import joblib
from sklearn.ensemble import GradientBoostingClassifier as SklearnGBC

from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class GradientBoostingClassifier(Classifier):
    def __init__(self, n_estimators: int = 100) -> None:
        self.n_estimators = n_estimators
        self.model = None

    def fit(self, data: list[tuple[Board, bool]]) -> float:
        raise NotImplementedError("Training is not supported in production environment")

        import numpy as np
        from sklearn.metrics import balanced_accuracy_score
        from sklearn.model_selection import train_test_split

        self.model = SklearnGBC(n_estimators=self.n_estimators)
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

    def load(self, filename: str) -> None:
        self.model = joblib.load(filename)
