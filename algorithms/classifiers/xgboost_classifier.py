import xgboost as xgb
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score
from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class XGBoostClassifier(Classifier):
    def __init__(self, num_boost_round: int = 100) -> None:
        self.num_boost_round = num_boost_round

    def fit(self, data: list[tuple[Board, bool]]) -> float:
        X = np.array([board.model_input().reshape(-1) for board, _ in data])
        y = np.array([int(label) for _, label in data])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y
        )

        self.model = xgb.XGBClassifier(
            objective="binary:logistic",
            n_estimators=self.num_boost_round,
            eval_metric="logloss"
        )
        self.model.fit(X_train, y_train)

        preds = self.model.predict(X_test)
        return balanced_accuracy_score(y_test, preds)

    def classify(self, board: Board) -> float:
        return float(self.model.predict_proba(board.model_input().reshape(1, -1))[0, 1])

    def save(self, filename: str) -> None:
        joblib.dump(self.model, filename)

    def load(self, filename: str) -> None:
        self.model = joblib.load(filename)
