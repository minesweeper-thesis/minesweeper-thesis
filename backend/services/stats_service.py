import uuid
from typing import Annotated, Literal

from fastapi import Depends
from fastapi_pagination import Page, Params

from backend.repositories import StatsRepository
from backend.schemas.stats_schemas import GameplayRanking, UserRanking


class StatsService:
    def __init__(self, repo: Annotated[StatsRepository, Depends()]):
        self.repo = repo

    async def get_gameplays_global_ranking(
        self,
        board_type_id: uuid.UUID,
        pagination_params: Params,
    ) -> Page[GameplayRanking]:
        return await self.repo.get_gameplays_global_ranking(
            board_type_id, pagination_params
        )

    async def get_gameplays_friends_ranking(
        self,
        user_id: uuid.UUID,
        board_type_id: uuid.UUID,
        pagination_params: Params,
    ) -> Page[GameplayRanking]:
        return await self.repo.get_gameplays_friends_ranking(
            user_id, board_type_id, pagination_params
        )

    async def get_users_global_ranking(
        self,
        board_type_id: uuid.UUID,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ) -> Page[UserRanking]:
        return await self.repo.get_global_user_ranking(
            board_type_id, sort_by, pagination_params
        )

    async def get_users_friends_ranking(
        self,
        user_id: uuid.UUID,
        board_type_id: uuid.UUID,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ) -> Page[UserRanking]:
        return await self.repo.get_friends_user_ranking(
            user_id, board_type_id, sort_by, pagination_params
        )
