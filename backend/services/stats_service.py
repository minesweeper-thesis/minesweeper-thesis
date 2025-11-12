import uuid
from typing import Annotated, Literal

from fastapi import Depends
from fastapi_pagination import Params

from backend.core.user import User
from backend.repositories import StatsRepository


class StatsService:
    def __init__(self, repo: Annotated[StatsRepository, Depends()]):
        self.repo = repo

    async def get_gameplays_global_ranking(
        self,
        difficulty_level_id: uuid.UUID,
        pagination_params: Params,
    ):
        return await self.repo.get_gameplays_global_ranking(
            difficulty_level_id, pagination_params
        )

    async def get_gameplays_friends_ranking(
        self,
        user: User,
        difficulty_level_id: uuid.UUID,
        pagination_params: Params,
    ):
        return await self.repo.get_gameplays_friends_ranking(
            user.id, difficulty_level_id, pagination_params
        )

    async def get_users_global_ranking(
        self,
        difficulty_level_id: uuid.UUID,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        return await self.repo.get_global_user_ranking(
            difficulty_level_id, sort_by, pagination_params
        )

    async def get_users_friends_ranking(
        self,
        user: User,
        difficulty_level_id: uuid.UUID,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        return await self.repo.get_friends_user_ranking(
            user.id, difficulty_level_id, sort_by, pagination_params
        )
