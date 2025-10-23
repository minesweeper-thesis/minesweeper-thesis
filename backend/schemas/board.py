from typing import Literal, Optional

from pydantic import BaseModel, Field

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
    generator_type: Literal["random", "ml_based"]
    generator_settings: Optional[GeneratorSettings] = Field(
        None, description="Required if generator_type is set to 'ml_based'"
    )
    difficulty_level: DifficultyLevel
    start_field: tuple[int, int]
