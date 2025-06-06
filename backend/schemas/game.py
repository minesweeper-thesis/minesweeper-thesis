import uuid

from pydantic import BaseModel


class GameplaySchema(BaseModel):
    board_id: uuid.UUID
    score: float
    time: float
    used_prompts: bool = False
