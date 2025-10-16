import uuid
from typing import Literal

from pydantic import BaseModel

Board = list[list[int]]


class Gameplay(BaseModel):
    board_id: uuid.UUID
    time: float
    used_prompts: bool = False
    won: bool


type ClassifierType = Literal[
    "lightgbm", "catboost", "gaussian", "mlp", "xgboost", "gradientboosting"
]
type HeuristicType = Literal["no", "naive", "GA", "MCTS", "PSO", "SA"]


class GeneratorInput(BaseModel):
    classifier: ClassifierType
    heuristic: HeuristicType
    heuristic_args: tuple[float | int, ...] = tuple()
    rows: int
    columns: int
    start_field: tuple[int, int]
    mine_count: int
