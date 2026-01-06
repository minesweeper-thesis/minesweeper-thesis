from typing import Optional

from algorithms.classifiers.base_classifier import BaseClassifier
from backend.core.board import ClassifierType, DifficultyLevel
from backend.lib.generator.model_loader import ModelLoader
from backend.lib.generator.onnx_classifier import OnnxClassifier


def get_classifier(
    difficulty_level: DifficultyLevel,
    classifier: Optional[ClassifierType] = None,
) -> Optional[BaseClassifier]:
    if classifier is None:
        return None
    version = _get_classifier_version(classifier, difficulty_level)
    model_loader = ModelLoader(
        difficulty_level.rows,
        difficulty_level.columns,
        difficulty_level.mine_count,
        classifier,
        version,
    )
    return OnnxClassifier.load(model_loader.get_model_path())


def _get_classifier_version(
    classifier: ClassifierType, difficulty_level: DifficultyLevel
) -> str:
    rows = difficulty_level.rows
    columns = difficulty_level.columns
    mine_count = difficulty_level.mine_count
    mapping = {
        (10, 10, 15, "lightgbm"): "12800",
        (16, 16, 40, "lightgbm"): "12800",
        (16, 30, 99, "lightgbm"): "400",
        (10, 10, 15, "catboost"): "6400",
        (16, 16, 40, "catboost"): "3200",
        (16, 30, 99, "catboost"): "1600",
        (10, 10, 15, "xgboost"): "6400",
        (16, 16, 40, "xgboost"): "6400",
        (16, 30, 99, "xgboost"): "3200",
        (10, 10, 15, "gaussiannb"): "",
        (16, 16, 40, "gaussiannb"): "",
        (16, 30, 99, "gaussiannb"): "",
    }

    key = (rows, columns, mine_count, classifier)

    if key not in mapping:
        raise ValueError(
            f"No classifier version found for {classifier} with difficulty {rows}x{columns} and {mine_count} mines"
        )

    return mapping[key]
