from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, Params

import backend.routers.schemas.stats_schemas as schemas
from backend import services
from backend.core.board import DifficultyLevel
from backend.lib.auth import CurrentUser
from backend.routers.schemas.user_schemas import UserResponse

StatsService = Annotated[services.StatsService, Depends()]
PaginationParams = Annotated[Params, Depends()]
CompareBy = Annotated[Literal["win_rate", "average_time"], Query()]

stats_router = APIRouter(prefix="/stats", tags=["stats"])


@stats_router.get(
    "/gameplays/global",
    responses={200: {"model": Page[schemas.GameplayRankingResponse]}},
)
async def get_gameplays_global_ranking(
    service: StatsService,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    pagination_params: PaginationParams,
):
    """Get global gameplays ranking sorted by time."""
    page = await service.get_gameplays_global_ranking(
        DifficultyLevel(rows, cols, mine_count), pagination_params
    )
    page.items = [
        schemas.GameplayRankingResponse(
            gameplay_id=item.gameplay_id,
            user=UserResponse.from_user(item.user),
            time=item.time,
        )
        for item in page.items
    ]
    return page


@stats_router.get(
    "/gameplays/friends",
    responses={200: {"model": Page[schemas.GameplayRankingResponse]}},
)
async def get_gameplays_friends_ranking(
    service: StatsService,
    user: CurrentUser,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    pagination_params: PaginationParams,
):
    """Get friends gameplays ranking sorted by time."""
    page = await service.get_gameplays_friends_ranking(
        user, DifficultyLevel(rows, cols, mine_count), pagination_params
    )
    page.items = [
        schemas.GameplayRankingResponse(
            gameplay_id=item.gameplay_id,
            user=UserResponse.from_user(item.user),
            time=item.time,
        )
        for item in page.items
    ]
    return page


@stats_router.get(
    "/users/global", responses={200: {"model": Page[schemas.UserRankingResponse]}}
)
async def get_users_global_ranking(
    service: StatsService,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    compare_by: CompareBy,
    pagination_params: PaginationParams,
):
    """Get global users ranking sorted by win rate or average time."""
    page = await service.get_users_global_ranking(
        DifficultyLevel(rows, cols, mine_count), compare_by, pagination_params
    )
    page.items = [
        schemas.UserRankingResponse(
            user=UserResponse.from_user(item.user),
            win_rate=item.win_rate,
            average_time=item.average_time,
            total_games=item.total_games,
            won_games=item.won_games,
        )
        for item in page.items
    ]
    return page


@stats_router.get(
    "/users/friends", responses={200: {"model": Page[schemas.UserRankingResponse]}}
)
async def get_users_friends_ranking(
    service: StatsService,
    user: CurrentUser,
    rows: Annotated[int, Query()],
    cols: Annotated[int, Query()],
    mine_count: Annotated[int, Query()],
    compare_by: CompareBy,
    pagination_params: PaginationParams,
):
    """Get friends users ranking sorted by win rate or average time."""
    page = await service.get_users_friends_ranking(
        user, DifficultyLevel(rows, cols, mine_count), compare_by, pagination_params
    )
    page.items = [
        schemas.UserRankingResponse(
            user=UserResponse.from_user(item.user),
            win_rate=item.win_rate,
            average_time=item.average_time,
            total_games=item.total_games,
            won_games=item.won_games,
        )
        for item in page.items
    ]
    return page
