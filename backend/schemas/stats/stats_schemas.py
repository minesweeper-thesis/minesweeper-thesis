import uuid

from pydantic import BaseModel, ConfigDict, field_validator

from backend.schemas.user import UserResponse


class GameplayRankingResponse(BaseModel):
    gameplay_id: uuid.UUID
    user: UserResponse
    time: float

    model_config = ConfigDict(from_attributes=True)

    @field_validator("time")
    @classmethod
    def round_average_time(cls, v):
        return round(v, 2)


class UserRankingResponse(BaseModel):
    user: UserResponse
    win_rate: float
    average_time: float
    total_games: int
    won_games: int

    model_config = ConfigDict(from_attributes=True)

    @field_validator("average_time")
    @classmethod
    def round_average_time(cls, v):
        return round(v, 2)


__all__ = ["GameplayRankingResponse", "UserRankingResponse"]
