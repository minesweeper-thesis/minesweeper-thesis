import uuid
from typing import Literal

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import Float, func, select

from backend.core.board import DifficultyLevel
from backend.core.user import User
from backend.db.db import DBSession
from backend.lib.online_users import get_online_users_store
from backend.repositories.orm import GameResultEnum, GameStatusEnum

from .orm import *


class TimeRankingItem:
    def __init__(self, gameplay_id: uuid.UUID, user: User, time: float):
        self.gameplay_id = gameplay_id
        self.user = user
        self.time = time


async def transform_time_ranking_items(items, is_online_func):
    result = []
    for item in items:
        is_online = await is_online_func(item[1].id)
        result.append(TimeRankingItem(item[0], item[1].to_user(is_online), item[2]))
    return result


class UserRankingItem:
    def __init__(
        self,
        user: User,
        win_rate: float,
        average_time: float,
        total_games: int,
        won_games: int,
    ):
        self.user = user
        self.win_rate = win_rate
        self.average_time = average_time
        self.total_games = total_games
        self.won_games = won_games


async def transform_user_ranking_items(items, is_online_func):
    result = []
    for item in items:
        is_online = await is_online_func(item[0].id)
        result.append(
            UserRankingItem(
                item[0].to_user(is_online), item[1], item[2], item[3], item[4]
            )
        )
    return result


class StatsRepository:
    def __init__(self, session: DBSession):
        self.session = session
        self.online_users_store = get_online_users_store()

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        return await self.online_users_store.is_user_online(user_id)

    async def get_difficulty_level_orm(
        self, difficulty_level: DifficultyLevel
    ) -> DifficultyLevelORM:
        stmt = select(DifficultyLevelORM).where(
            DifficultyLevelORM.rows == difficulty_level.rows,
            DifficultyLevelORM.columns == difficulty_level.columns,
            DifficultyLevelORM.mine_count == difficulty_level.mine_count,
        )
        result = await self.session.execute(stmt)
        difficulty_level_orm = result.scalar_one_or_none()

        if difficulty_level_orm is None:
            difficulty_level_orm = DifficultyLevelORM(
                rows=difficulty_level.rows,
                columns=difficulty_level.columns,
                mine_count=difficulty_level.mine_count,
            )
            self.session.add(difficulty_level_orm)
            await self.session.commit()
            await self.session.refresh(difficulty_level_orm)

        return difficulty_level_orm

    async def get_gameplays_global_ranking(
        self,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.get_difficulty_level_orm(difficulty_level)

        stmt = (
            select(
                SingleplayerGameplayORM.id.label("gameplay_id"),
                UserORM,
                SingleplayerGameplayORM.time,
            )
            .join(UserORM, SingleplayerGameplayORM.user_id == UserORM.id)
            .join(BoardORM, SingleplayerGameplayORM.board_id == BoardORM.id)
            .where(
                BoardORM.difficulty_level_id == difficulty_level_orm.id,
            )
            .where(SingleplayerGameplayORM.used_hints == False)
            .order_by(SingleplayerGameplayORM.time.asc())
        )

        async def async_transformer(items):
            return await transform_time_ranking_items(items, self.is_user_online)

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=async_transformer,
        )

    async def get_gameplays_friends_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.get_difficulty_level_orm(difficulty_level)

        stmt = (
            select(
                SingleplayerGameplayORM.id.label("gameplay_id"),
                UserORM,
                SingleplayerGameplayORM.time,
            )
            .join(UserORM, SingleplayerGameplayORM.user_id == UserORM.id)
            .join(BoardORM, SingleplayerGameplayORM.board_id == BoardORM.id)
            .outerjoin(
                FriendshipORM,
                (FriendshipORM.friend_id == UserORM.id)
                & (FriendshipORM.user_id == user_id),
            )
            .where(
                BoardORM.difficulty_level_id == difficulty_level_orm.id,
            )
            .where(SingleplayerGameplayORM.used_hints == False)
            .where((UserORM.id == user_id) | (FriendshipORM.friend_id == UserORM.id))
            .order_by(SingleplayerGameplayORM.time.asc())
        )

        async def async_transformer(items):
            return await transform_time_ranking_items(items, self.is_user_online)

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=async_transformer,
        )

    async def get_global_user_ranking(
        self,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.get_difficulty_level_orm(difficulty_level)

        stmt = (
            select(
                UserORM,
                (
                    func.cast(
                        func.count().filter(
                            SingleplayerGameplayORM.result == GameResultEnum.win
                        ),
                        Float,
                    )
                    / func.count(SingleplayerGameplayORM.id)
                ).label("win_rate"),
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == GameStatusEnum.finished
                    ),
                    0.0,
                ).label("average_time"),
                func.count(SingleplayerGameplayORM.id).label("total_games"),
                func.count()
                .filter(SingleplayerGameplayORM.result == GameResultEnum.win)
                .label("won_games"),
            )
            .join(
                SingleplayerGameplayORM, SingleplayerGameplayORM.user_id == UserORM.id
            )
            .join(BoardORM, SingleplayerGameplayORM.board_id == BoardORM.id)
            .where(
                BoardORM.difficulty_level_id == difficulty_level_orm.id,
            )
            .where(SingleplayerGameplayORM.used_hints == False)
            .group_by(UserORM.id)
        )

        if sort_by == "win_rate":
            stmt = stmt.order_by(
                (
                    func.cast(
                        func.count().filter(
                            SingleplayerGameplayORM.result == GameResultEnum.win
                        ),
                        Float,
                    )
                    / func.count(SingleplayerGameplayORM.id)
                ).desc()
            )
        else:
            stmt = stmt.order_by(
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == GameStatusEnum.finished
                    ),
                    0.0,
                ).asc()
            )

        async def async_transformer(items):
            return await transform_user_ranking_items(items, self.is_user_online)

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=async_transformer,
        )

    async def get_friends_user_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.get_difficulty_level_orm(difficulty_level)

        stmt = (
            select(
                UserORM,
                (
                    func.cast(
                        func.count().filter(
                            SingleplayerGameplayORM.result == GameResultEnum.win
                        ),
                        Float,
                    )
                    / func.count(SingleplayerGameplayORM.id)
                ).label("win_rate"),
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == GameStatusEnum.finished
                    ),
                    0.0,
                ).label("average_time"),
                func.count(SingleplayerGameplayORM.id).label("total_games"),
                func.count()
                .filter(SingleplayerGameplayORM.result == GameResultEnum.win)
                .label("won_games"),
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
            .where(
                BoardORM.difficulty_level_id == difficulty_level_orm.id,
            )
            .where(SingleplayerGameplayORM.used_hints == False)
            .group_by(UserORM.id)
        )

        if sort_by == "win_rate":
            stmt = stmt.order_by(
                (
                    func.cast(
                        func.count().filter(
                            SingleplayerGameplayORM.result == GameResultEnum.win
                        ),
                        Float,
                    )
                    / func.count(SingleplayerGameplayORM.id)
                ).desc()
            )
        else:
            stmt = stmt.order_by(
                func.coalesce(
                    func.avg(SingleplayerGameplayORM.time).filter(
                        SingleplayerGameplayORM.status == GameStatusEnum.finished
                    ),
                    0.0,
                ).asc()
            )

        async def async_transformer(items):
            return await transform_user_ranking_items(items, self.is_user_online)

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=async_transformer,
        )
