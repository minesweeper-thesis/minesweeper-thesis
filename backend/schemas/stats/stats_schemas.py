import uuid

from pydantic import BaseModel, ConfigDict

from backend.schemas.user import UserResponse


class GameplayRankingResponse(BaseModel):
    gameplay_id: uuid.UUID
    user: UserResponse
    time: float

    model_config = ConfigDict(from_attributes=True)


class UserRankingResponse(BaseModel):
    user: UserResponse
    win_rate: float
    average_time: float
    total_games: int
    won_games: int

    model_config = ConfigDict(from_attributes=True)


__all__ = ["GameplayRankingResponse", "UserRankingResponse"]
