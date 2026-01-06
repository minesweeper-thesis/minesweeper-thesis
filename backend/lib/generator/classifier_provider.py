from typing import Optional

from algorithms.classifiers.base_classifier import BaseClassifier
from algorithms.generator import HeuristicType
from backend.core.board import ClassifierType, DifficultyLevel
from backend.lib.generator.model_loader import ModelLoader
from backend.lib.generator.onnx_classifier import OnnxClassifier


def get_classifier(
    difficulty_level: DifficultyLevel,
    classifier: Optional[ClassifierType] = None,
    heuristic: Optional[HeuristicType] = None,
) -> Optional[BaseClassifier]:
    if classifier is None or heuristic is None:
        return None
    version = _get_classifier_version(classifier, heuristic, difficulty_level)
    model_loader = ModelLoader(
        difficulty_level.rows,
        difficulty_level.columns,
        difficulty_level.mine_count,
        classifier,
        version,
    )
    return OnnxClassifier.load(model_loader.get_model_path())


def _get_classifier_version(
    classifier: ClassifierType,
    heuristic: HeuristicType,
    difficulty_level: DifficultyLevel,
) -> str:
    rows = difficulty_level.rows
    columns = difficulty_level.columns
    mine_count = difficulty_level.mine_count

    key = (rows, columns, mine_count, classifier, heuristic)

    if key not in CLASSIFIER_VERSION:
        raise ValueError(
            f"No classifier version found for {classifier} with difficulty {rows}x{columns} and {mine_count} mines"
        )

    return CLASSIFIER_VERSION[key]


CLASSIFIER_VERSION = {
    (10, 10, 15, "lightgbm", "naive"): "800",
    (10, 10, 15, "lightgbm", "GA"): "100",
    (10, 10, 15, "lightgbm", "PSO"): "800",
    (10, 10, 15, "lightgbm", "SA"): "800",
    (16, 16, 40, "lightgbm", "naive"): "100",
    (16, 16, 40, "lightgbm", "GA"): "100",
    (16, 16, 40, "lightgbm", "PSO"): "800",
    (16, 16, 40, "lightgbm", "SA"): "800",
    (16, 30, 99, "lightgbm", "naive"): "100",
    (16, 30, 99, "lightgbm", "GA"): "400",
    (16, 30, 99, "lightgbm", "PSO"): "100",
    (16, 30, 99, "lightgbm", "SA"): "400",
    (10, 10, 15, "catboost", "naive"): "100",
    (10, 10, 15, "catboost", "GA"): "800",
    (10, 10, 15, "catboost", "PSO"): "800",
    (10, 10, 15, "catboost", "SA"): "800",
    (16, 16, 40, "catboost", "naive"): "3200",
    (16, 16, 40, "catboost", "GA"): "100",
    (16, 16, 40, "catboost", "PSO"): "3200",
    (16, 16, 40, "catboost", "SA"): "400",
    (16, 30, 99, "catboost", "naive"): "1600",
    (16, 30, 99, "catboost", "GA"): "1600",
    (16, 30, 99, "catboost", "PSO"): "1600",
    (16, 30, 99, "catboost", "SA"): "1600",
    (10, 10, 15, "xgboost", "naive"): "100",
    (10, 10, 15, "xgboost", "GA"): "800",
    (10, 10, 15, "xgboost", "PSO"): "6400",
    (10, 10, 15, "xgboost", "SA"): "100",
    (16, 16, 40, "xgboost", "naive"): "100",
    (16, 16, 40, "xgboost", "GA"): "100",
    (16, 16, 40, "xgboost", "PSO"): "800",
    (16, 16, 40, "xgboost", "SA"): "800",
    (16, 30, 99, "xgboost", "naive"): "3200",
    (16, 30, 99, "xgboost", "GA"): "3200",
    (16, 30, 99, "xgboost", "PSO"): "3200",
    (16, 30, 99, "xgboost", "SA"): "400",
    (10, 10, 15, "gaussiannb", "naive"): "",
    (10, 10, 15, "gaussiannb", "GA"): "",
    (10, 10, 15, "gaussiannb", "PSO"): "",
    (10, 10, 15, "gaussiannb", "SA"): "",
    (16, 16, 40, "gaussiannb", "naive"): "",
    (16, 16, 40, "gaussiannb", "GA"): "",
    (16, 16, 40, "gaussiannb", "PSO"): "",
    (16, 16, 40, "gaussiannb", "SA"): "",
    (16, 30, 99, "gaussiannb", "naive"): "",
    (16, 30, 99, "gaussiannb", "GA"): "",
    (16, 30, 99, "gaussiannb", "PSO"): "",
    (16, 30, 99, "gaussiannb", "SA"): "",
    (10, 10, 15, "mlp", "naive"): "(32,16)",
    (10, 10, 15, "mlp", "GA"): "(32,16)",
    (10, 10, 15, "mlp", "PSO"): "(32,16)",
    (10, 10, 15, "mlp", "SA"): "(32,16)",
    (16, 16, 40, "mlp", "naive"): "(16,)",
    (16, 16, 40, "mlp", "GA"): "(16,)",
    (16, 16, 40, "mlp", "PSO"): "(64,64)",
    (16, 16, 40, "mlp", "SA"): "(256,)",
    (16, 30, 99, "mlp", "naive"): "(256,)",
    (16, 30, 99, "mlp", "GA"): "(256,)",
    (16, 30, 99, "mlp", "PSO"): "(256,)",
    (16, 30, 99, "mlp", "SA"): "(64,)",
}
