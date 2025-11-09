import joblib
from sklearn.neural_network import MLPClassifier as SklearnMLPClassifier

from algorithms.boards.base_board import BaseBoard
from algorithms.classifiers.classifier import BaseClassifier


class MLPClassifier(BaseClassifier):
    def __init__(self, hidden_layer_sizes=(100,), max_iter=200) -> None:
        super().__init__()
        self.hidden_layer_sizes = hidden_layer_sizes
        self.max_iter = max_iter

    def fit(self, data: list[tuple[BaseBoard, bool]]) -> float:
        if self.model:
            raise RuntimeError("Model already loaded.")

        import numpy as np
        from sklearn.metrics import balanced_accuracy_score
        from sklearn.model_selection import train_test_split

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

    def classify(self, board: BaseBoard) -> float:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        return float(self.model.predict_proba(board.model_input().reshape(1, -1))[0][1])

    def save(self, filename: str) -> None:
        joblib.dump(self.model, filename)
