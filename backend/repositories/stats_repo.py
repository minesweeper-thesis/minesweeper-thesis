import uuid
from typing import Annotated, Literal

from fastapi import Depends
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import Board, Friendship, Gameplay, User


class StatsRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_async_session)]):
        self.session = session

    async def get_gameplays_global_ranking(
        self,
        board_type_id: uuid.UUID,
        pagination_params: Params,
    ):
        stmt = (
            select(
                Gameplay.id.label("gameplay_id"),
                User.id.label("user_id"),
                User.nickname,
                Gameplay.time,
            )
            .join(User, Gameplay.user_id == User.id)
            .join(Board, Gameplay.board_id == Board.id)
            .where(Board.board_type_id == board_type_id)
            .where(Gameplay.used_prompts == False)
            .order_by(Gameplay.time.asc())
        )

        return await apaginate(self.session, stmt, pagination_params)

    async def get_gameplays_friends_ranking(
        self,
        user_id: uuid.UUID,
        board_type_id: uuid.UUID,
        pagination_params: Params,
    ):
        stmt = (
            select(
                Gameplay.id.label("gameplay_id"),
                User.id.label("user_id"),
                User.nickname,
                Gameplay.time,
            )
            .join(User, Gameplay.user_id == User.id)
            .join(Board, Gameplay.board_id == Board.id)
            .join(
                Friendship,
                (Friendship.friend_id == User.id) & (Friendship.user_id == user_id),
            )
            .where(Board.board_type_id == board_type_id)
            .where(Gameplay.used_prompts == False)
            .order_by(Gameplay.time.asc())
        )

        return await apaginate(self.session, stmt, pagination_params)

    async def get_global_user_ranking(
        self,
        board_type_id: uuid.UUID,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        stmt = (
            select(
                User.id.label("user_id"),
                User.nickname,
                (
                    func.cast(func.count(Gameplay.won), Float) / func.count(Gameplay.id)
                ).label("win_rate"),
                func.avg(Gameplay.time)
                .filter(Gameplay.won == True)
                .label("average_time"),
                func.count(Gameplay.id).label("total_games"),
                func.count(Gameplay.won).label("won_games"),
            )
            .join(Gameplay, Gameplay.user_id == User.id)
            .join(Board, Gameplay.board_id == Board.id)
            .where(Board.board_type_id == board_type_id)
            .where(Gameplay.used_prompts == False)
            .group_by(User.id)
        )

        if sort_by == "win_rate":
            stmt = stmt.order_by(
                (
                    func.cast(func.count(Gameplay.won), Float) / func.count(Gameplay.id)
                ).desc()
            )
        else:
            stmt = stmt.order_by(
                func.avg(Gameplay.time).filter(Gameplay.won == True).asc()
            )

        return await apaginate(self.session, stmt, pagination_params)

    async def get_friends_user_ranking(
        self,
        user_id: uuid.UUID,
        board_type_id: uuid.UUID,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        stmt = (
            select(
                User.id.label("user_id"),
                User.nickname,
                (
                    func.cast(func.count(Gameplay.won), Float) / func.count(Gameplay.id)
                ).label("win_rate"),
                func.avg(Gameplay.time)
                .filter(Gameplay.won == True)
                .label("average_time"),
                func.count(Gameplay.id).label("total_games"),
                func.count(Gameplay.won).label("won_games"),
            )
            .join(Gameplay, Gameplay.user_id == User.id)
            .join(Board, Gameplay.board_id == Board.id)
            .join(
                Friendship,
                (Friendship.friend_id == User.id) & (Friendship.user_id == user_id),
            )
            .where(Board.board_type_id == board_type_id)
            .where(Gameplay.used_prompts == False)
            .group_by(User.id)
        )

        if sort_by == "win_rate":
            stmt = stmt.order_by(
                (
                    func.cast(func.count(Gameplay.won), Float) / func.count(Gameplay.id)
                ).desc()
            )
        else:
            stmt = stmt.order_by(
                func.avg(Gameplay.time).filter(Gameplay.won == True).asc()
            )

        return await apaginate(self.session, stmt, pagination_params)
