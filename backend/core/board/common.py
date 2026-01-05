from dataclasses import dataclass
from typing import Literal, Optional, Self

type ClassifierType = Literal["lightgbm", "catboost", "gaussiannb", "xgboost"]
type HeuristicType = Literal["no", "naive", "GA", "PSO", "SA"]
type GeneratorType = Literal["random", "ml"]


@dataclass
class DifficultyLevel:
    rows: int
    columns: int
    mine_count: int

    @classmethod
    def easy(cls) -> Self:
        return cls(rows=10, columns=10, mine_count=15)

    @classmethod
    def medium(cls) -> Self:
        return cls(rows=16, columns=16, mine_count=40)

    @classmethod
    def hard(cls) -> Self:
        return cls(rows=16, columns=30, mine_count=99)


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
