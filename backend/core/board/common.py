from dataclasses import dataclass
from typing import Literal, Optional

type ClassifierType = Literal["lightgbm", "catboost", "gaussiannb", "xgboost"]
type HeuristicType = Literal["no", "naive", "GA", "PSO", "SA"]
type GeneratorType = Literal["random", "ml"]


@dataclass
class DifficultyLevel:
    rows: int
    columns: int
    mine_count: int


@dataclass
class GeneratorParams:
    classifier: ClassifierType
    heuristic: HeuristicType = "no"
    heuristic_args: tuple[float | int, ...] = tuple()


@dataclass
class GenerationSettings:
    type: GeneratorType
    difficulty_level: DifficultyLevel
    settings: Optional[GeneratorParams] = None


__all__ = [
    "ClassifierType",
    "HeuristicType",
    "GeneratorType",
    "DifficultyLevel",
    "GeneratorParams",
    "GenerationSettings",
]
