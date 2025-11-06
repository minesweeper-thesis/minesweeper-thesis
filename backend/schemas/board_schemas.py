from typing import Literal, Optional

from pydantic import BaseModel, Field

type ClassifierType = Literal["lightgbm", "catboost", "gaussiannb", "xgboost"]
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
    type: Literal["random", "ml"]
    settings: Optional[GeneratorSettings] = Field(
        None, description="Required if generator_type is set to 'ml'"
    )
