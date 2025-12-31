import logging
from typing import Literal

from fastapi_pagination import Params

from backend.core.board import DifficultyLevel
from backend.core.user import User
from backend.di.dependencies import *

logger = logging.getLogger(__name__)


class StatsService:
    def __init__(self, stats_repo: StatsRepositoryDep, board_repo: BoardRepositoryDep):
        self.repo = stats_repo
        self.board_repo = board_repo

    async def get_gameplays_global_ranking(
        self,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        logger.debug(
            f"Getting global gameplays ranking for difficulty {difficulty_level.rows}x{difficulty_level.columns}"
        )
        return await self.repo.get_gameplays_global_ranking(
            difficulty_level, pagination_params
        )

    async def get_gameplays_friends_ranking(
        self,
        user: User,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        return await self.repo.get_gameplays_friends_ranking(
            user.id, difficulty_level, pagination_params
        )

    async def get_users_global_ranking(
        self,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        return await self.repo.get_global_user_ranking(
            difficulty_level, sort_by, pagination_params
        )

    async def get_users_friends_ranking(
        self,
        user: User,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        return await self.repo.get_friends_user_ranking(
            user.id, difficulty_level, sort_by, pagination_params
        )


__all__ = ["StatsService"]
