import uuid
from typing import Literal

from pydantic import BaseModel

BoardSchema = list[list[int]]


class GameplaySchema(BaseModel):
    board_id: uuid.UUID
    score: float
    time: float
    used_prompts: bool = False


type ClassifierType = Literal[
    "lightgbm", "catboost", "gaussian", "mlp", "xgboost", "gradientboosting"
]
type HeuristicType = Literal["no", "naive", "GA", "MCTS", "PSO", "SA"]


class GeneratorInputSchema(BaseModel):
    classifier: ClassifierType
    heuristic: HeuristicType
    heuristic_args: tuple[float | int, ...] = tuple()
    rows: int
    columns: int
    start_field: tuple[int, int]
    mine_count: int
