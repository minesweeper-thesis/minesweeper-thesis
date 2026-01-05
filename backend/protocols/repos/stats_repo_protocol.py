import uuid
from typing import Literal, Protocol

from fastapi_pagination import Params

from backend.core.board import DifficultyLevel


class StatsRepository(Protocol):
    async def get_gameplays_global_ranking(
        self, difficulty_level: DifficultyLevel, pagination_params: Params
    ): ...

    async def get_gameplays_friends_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ): ...

    async def get_global_user_ranking(
        self,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ): ...

    async def get_friends_user_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ): ...


__all__ = ["StatsRepository"]
