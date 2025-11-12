import uuid

from pydantic import BaseModel, ConfigDict


class GameplayRankingResponse(BaseModel):
    gameplay_id: uuid.UUID
    user_id: uuid.UUID
    nickname: str
    time: float

    model_config = ConfigDict(from_attributes=True)


class UserRankingResponse(BaseModel):
    user_id: uuid.UUID
    nickname: str
    win_rate: float
    average_time: float
    total_games: int
    won_games: int

    model_config = ConfigDict(from_attributes=True)
