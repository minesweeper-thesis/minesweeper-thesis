import uuid
from typing import Literal, Optional

from pydantic import BaseModel

type ClassifierType = Literal[
    "lightgbm", "catboost", "gaussian", "mlp", "xgboost", "gradientboosting"
]
type HeuristicType = Literal["no", "naive", "GA", "MCTS", "PSO", "SA"]


class DifficultyLevel(BaseModel):
    rows: int
    columns: int
    mine_count: int


class GeneratorSettings(BaseModel):
    classifier: ClassifierType
    heuristic: HeuristicType
    heuristic_args: tuple[float | int, ...] = tuple()


class GenerationInput(BaseModel):
    generator_type: Literal["random", "deterministic"]
    generator_settings: Optional[GeneratorSettings] = None
    difficulty_level: DifficultyLevel
    start_field: tuple[int, int]


class GenerationOutput(BaseModel):
    board_id: uuid.UUID
