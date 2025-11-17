from typing import Annotated, Literal

from fastapi import Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core.board import DifficultyLevel
from backend.core.user import User

StatsRepository = Annotated[repositories.StatsRepository, Depends()]


class StatsService:
    def __init__(self, repo: StatsRepository):
        self.repo = repo

    async def get_gameplays_global_ranking(
        self,
        rows: int,
        cols: int,
        mine_count: int,
        pagination_params: Params,
    ):
        difficulty_level = DifficultyLevel(
            rows=rows, columns=cols, mine_count=mine_count
        )
        return await self.repo.get_gameplays_global_ranking(
            difficulty_level, pagination_params
        )

    async def get_gameplays_friends_ranking(
        self,
        user: User,
        rows: int,
        cols: int,
        mine_count: int,
        pagination_params: Params,
    ):
        difficulty_level = DifficultyLevel(
            rows=rows, columns=cols, mine_count=mine_count
        )
        return await self.repo.get_gameplays_friends_ranking(
            user.id, difficulty_level, pagination_params
        )

    async def get_users_global_ranking(
        self,
        rows: int,
        cols: int,
        mine_count: int,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level = DifficultyLevel(
            rows=rows, columns=cols, mine_count=mine_count
        )
        return await self.repo.get_global_user_ranking(
            difficulty_level, sort_by, pagination_params
        )

    async def get_users_friends_ranking(
        self,
        user: User,
        rows: int,
        cols: int,
        mine_count: int,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level = DifficultyLevel(
            rows=rows, columns=cols, mine_count=mine_count
        )
        return await self.repo.get_friends_user_ranking(
            user.id, difficulty_level, sort_by, pagination_params
        )
