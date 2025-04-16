import lightgbm as lgb
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score
from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class LightGBMClassifier(Classifier):
    def fit(self, data: list[tuple[Board, bool]]) -> float:
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
        )

        preds = self.model.predict(X_test)
        preds_binary = (preds > 0.5).astype(int)
        return balanced_accuracy_score(y_test, preds_binary)

    def classify(self, board: Board) -> float:
        arr = board.model_input().reshape(1, -1)
        return float(self.model.predict(arr)[0])

    def save(self, filename: str) -> None:
        if not os.path.exists(filename):
            open(filename, 'a').close()
        joblib.dump(self.model, filename)

    def load(self, filename: str) -> None:
        self.model = joblib.load(filename)