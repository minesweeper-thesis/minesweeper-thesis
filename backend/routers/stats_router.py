import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, Params

from backend import schemas, services
from backend.services.auth_service import CurrentUser

StatsService = Annotated[services.StatsService, Depends()]
PaginationParams = Annotated[Params, Depends()]
CompareBy = Annotated[Literal["win_rate", "average_time"], Query()]

stats_router = APIRouter(prefix="/stats", tags=["stats"])


@stats_router.get("/gameplays-ranking/{board_type_id}/global")
async def get_gameplays_global_ranking(
    service: StatsService,
    board_type_id: uuid.UUID,
    pagination_params: PaginationParams,
) -> Page[schemas.GameplayRanking]:
    """Get global gameplays ranking sorted by time."""
    return await service.get_gameplays_global_ranking(board_type_id, pagination_params)


@stats_router.get("/gameplays-ranking/{board_type_id}/friends")
async def get_gameplays_friends_ranking(
    service: StatsService,
    user: CurrentUser,
    board_type_id: uuid.UUID,
    pagination_params: PaginationParams,
) -> Page[schemas.GameplayRanking]:
    """Get friends gameplays ranking sorted by time."""
    return await service.get_gameplays_friends_ranking(
        user.id, board_type_id, pagination_params
    )


@stats_router.get("/users-ranking/{board_type_id}/global")
async def get_users_global_ranking(
    service: StatsService,
    board_type_id: uuid.UUID,
    compare_by: CompareBy,
    pagination_params: PaginationParams,
) -> Page[schemas.UserRanking]:
    """Get global users ranking sorted by win rate or average time."""
    return await service.get_users_global_ranking(
        board_type_id, compare_by, pagination_params
    )


@stats_router.get("/users-ranking/{board_type_id}/friends")
async def get_users_friends_ranking(
    service: StatsService,
    user: CurrentUser,
    board_type_id: uuid.UUID,
    compare_by: CompareBy,
    pagination_params: PaginationParams,
) -> Page[schemas.UserRanking]:
    """Get friends users ranking sorted by win rate or average time."""
    return await service.get_users_friends_ranking(
        user.id, board_type_id, compare_by, pagination_params
    )
