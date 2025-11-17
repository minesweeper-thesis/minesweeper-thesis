import uuid
from typing import Literal

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import Float, func, select

from backend.core.board import DifficultyLevel
from backend.db.db import DBSession
from backend.repositories.utils import _get_difficulty_level_orm

from .orm import *


class StatsRepository:
    def __init__(self, session: DBSession):
        self.session = session

    async def get_gameplays_global_ranking(
        self,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        difficulty_level_orm = await _get_difficulty_level_orm(self, difficulty_level)
        stmt = (
            select(
                SingleplayerGameplayORM.id.label("gameplay_id"),
                UserORM.id.label("user_id"),
                UserORM.nickname,
                SingleplayerGameplayORM.time,
            )
            .join(UserORM, SingleplayerGameplayORM.user_id == UserORM.id)
            .join(BoardORM, SingleplayerGameplayORM.board_id == BoardORM.id)
            .where(BoardORM.difficulty_level_id == difficulty_level_orm.id)
            .where(SingleplayerGameplayORM.used_hints == False)
            .order_by(SingleplayerGameplayORM.time.asc())
        )

        return await apaginate(self.session, stmt, pagination_params)

    async def get_gameplays_friends_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        difficulty_level_orm = await _get_difficulty_level_orm(self, difficulty_level)
        stmt = (
            select(
                SingleplayerGameplayORM.id.label("gameplay_id"),
                UserORM.id.label("user_id"),
                UserORM.nickname,
                SingleplayerGameplayORM.time,
            )
            .join(UserORM, SingleplayerGameplayORM.user_id == UserORM.id)
            .join(BoardORM, SingleplayerGameplayORM.board_id == BoardORM.id)
            .join(
                FriendshipORM,
                (FriendshipORM.friend_id == UserORM.id)
                & (FriendshipORM.user_id == user_id),
            )
            .where(BoardORM.difficulty_level_id == difficulty_level_orm.id)
            .where(SingleplayerGameplayORM.used_hints == False)
            .order_by(SingleplayerGameplayORM.time.asc())
        )

        return await apaginate(self.session, stmt, pagination_params)

    async def get_global_user_ranking(
        self,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level_orm = await _get_difficulty_level_orm(self, difficulty_level)
        stmt = (
            select(
                UserORM.id.label("user_id"),
                UserORM.nickname,
                (
                    func.cast(func.count(SingleplayerGameplayORM.result), Float)
                    / func.count(SingleplayerGameplayORM.id)
                ).label("win_rate"),
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == True
                    ),
                    0.0,
                ).label("average_time"),
                func.count(SingleplayerGameplayORM.id).label("total_games"),
                func.count(SingleplayerGameplayORM.result).label("won_games"),
            )
            .join(
                SingleplayerGameplayORM, SingleplayerGameplayORM.user_id == UserORM.id
            )
            .join(BoardORM, SingleplayerGameplayORM.board_id == BoardORM.id)
            .where(BoardORM.difficulty_level_id == difficulty_level_orm.id)
            .where(SingleplayerGameplayORM.used_hints == False)
            .group_by(UserORM.id)
        )

        if sort_by == "win_rate":
            stmt = stmt.order_by(
                (
                    func.cast(func.count(SingleplayerGameplayORM.result), Float)
                    / func.count(SingleplayerGameplayORM.id)
                ).desc()
            )
        else:
            stmt = stmt.order_by(
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == True
                    ),
                    0.0,
                ).asc()
            )

        return await apaginate(self.session, stmt, pagination_params)

    async def get_friends_user_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level_orm = await _get_difficulty_level_orm(self, difficulty_level)
        stmt = (
            select(
                UserORM.id.label("user_id"),
                UserORM.nickname,
                (
                    func.cast(func.count(SingleplayerGameplayORM.result), Float)
                    / func.count(SingleplayerGameplayORM.id)
                ).label("win_rate"),
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == True
                    ),
                    0.0,
                ).label("average_time"),
                func.count(SingleplayerGameplayORM.id).label("total_games"),
                func.count(SingleplayerGameplayORM.result).label("won_games"),
            )
            .join(
                SingleplayerGameplayORM, SingleplayerGameplayORM.user_id == UserORM.id
            )
            .join(BoardORM, SingleplayerGameplayORM.board_id == BoardORM.id)
            .join(
                FriendshipORM,
                (FriendshipORM.friend_id == UserORM.id)
                & (FriendshipORM.user_id == user_id),
            )
            .where(BoardORM.difficulty_level_id == difficulty_level_orm.id)
            .where(SingleplayerGameplayORM.used_hints == False)
            .group_by(UserORM.id)
        )

        if sort_by == "win_rate":
            stmt = stmt.order_by(
                (
                    func.cast(func.count(SingleplayerGameplayORM.result), Float)
                    / func.count(SingleplayerGameplayORM.id)
                ).desc()
            )
        else:
            stmt = stmt.order_by(
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == True
                    ),
                    0.0,
                ).asc()
            )

        return await apaginate(self.session, stmt, pagination_params)
