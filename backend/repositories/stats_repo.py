import uuid
from typing import Annotated, Literal

from fastapi import Depends
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import Float, func, select

from backend import repositories
from backend.core.board import DifficultyLevel
from backend.core.user import User
from backend.db.db import DBSession
from backend.repositories.orm.game_orm import GameResultEnum, GameStatusEnum

from .orm import *

BoardRepository = Annotated[repositories.BoardRepository, Depends()]


class TimeRankingItem:
    def __init__(self, gameplay_id: uuid.UUID, user: User, time: float):
        self.gameplay_id = gameplay_id
        self.user = user
        self.time = time


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


class StatsRepository:
    def __init__(self, session: DBSession, board_repo: BoardRepository):
        self.session = session
        self.board_repo = board_repo

    async def get_gameplays_global_ranking(
        self,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.board_repo.get_difficulty_level_orm(
            difficulty_level
        )

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

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=lambda items: [
                TimeRankingItem(item[0], item[1].to_user(), item[2]) for item in items
            ],
        )

    async def get_gameplays_friends_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.board_repo.get_difficulty_level_orm(
            difficulty_level
        )

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

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=lambda items: [
                TimeRankingItem(item[0], item[1].to_user(), item[2]) for item in items
            ],
        )

    async def get_global_user_ranking(
        self,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.board_repo.get_difficulty_level_orm(
            difficulty_level
        )

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

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=lambda items: [
                UserRankingItem(
                    item[0].to_user(),
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                )
                for item in items
            ],
        )

    async def get_friends_user_ranking(
        self,
        user_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        sort_by: Literal["win_rate", "average_time"],
        pagination_params: Params,
    ):
        difficulty_level_orm = await self.board_repo.get_difficulty_level_orm(
            difficulty_level
        )

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

        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=lambda items: [
                UserRankingItem(
                    item[0].to_user(),
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                )
                for item in items
            ],
        )
