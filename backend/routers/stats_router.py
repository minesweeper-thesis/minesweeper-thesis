from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, Params

import backend.routers.schemas.stats_schemas as schemas
from backend import services
from backend.lib.auth import CurrentUser

StatsService = Annotated[services.StatsService, Depends()]
PaginationParams = Annotated[Params, Depends()]
CompareBy = Annotated[Literal["win_rate", "average_time"], Query()]

stats_router = APIRouter(prefix="/stats", tags=["stats"])


@stats_router.get("/gameplays/global")
async def get_gameplays_global_ranking(
    service: StatsService,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    pagination_params: PaginationParams,
) -> Page[schemas.GameplayRankingResponse]:
    """Get global gameplays ranking sorted by time."""
    return await service.get_gameplays_global_ranking(
        rows, cols, mine_count, pagination_params
    )


@stats_router.get("/gameplays/friends")
async def get_gameplays_friends_ranking(
    service: StatsService,
    user: CurrentUser,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    pagination_params: PaginationParams,
) -> Page[schemas.GameplayRankingResponse]:
    """Get friends gameplays ranking sorted by time."""
    return await service.get_gameplays_friends_ranking(
        user, rows, cols, mine_count, pagination_params
    )


@stats_router.get("/users/global")
async def get_users_global_ranking(
    service: StatsService,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    compare_by: CompareBy,
    pagination_params: PaginationParams,
) -> Page[schemas.UserRankingResponse]:
    """Get global users ranking sorted by win rate or average time."""
    return await service.get_users_global_ranking(
        rows, cols, mine_count, compare_by, pagination_params
    )


@stats_router.get("/users/friends")
async def get_users_friends_ranking(
    service: StatsService,
    user: CurrentUser,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    compare_by: CompareBy,
    pagination_params: PaginationParams,
) -> Page[schemas.UserRankingResponse]:
    """Get friends users ranking sorted by win rate or average time."""
    return await service.get_users_friends_ranking(
        user, rows, cols, mine_count, compare_by, pagination_params
    )
