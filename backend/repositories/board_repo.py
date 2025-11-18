import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import func

from backend.core.board import Board, DifficultyLevel
from backend.core.user import User
from backend.db.db import DBSession
from backend.repositories.utils import get_difficulty_level_orm

from .exceptions import *
from .orm import *


class BoardRepository:
    def __init__(self, session: DBSession):
        self.session = session

    async def add_board(self, board: Board) -> None:
        difficulty_level_orm = await get_difficulty_level_orm(
            self, board.difficulty_level
        )
        board_orm = BoardORM.from_board(board, difficulty_level_orm.id)

        self.session.add(board_orm)
        await self.session.commit()

    async def get_board_by_id(self, board_id: uuid.UUID) -> Board:
        try:
            stmt = (
                select(BoardORM)
                .where(BoardORM.id == board_id)
                .options(selectinload(BoardORM.difficulty_level))
            )
            result = await self.session.execute(stmt)
            return result.scalar_one().to_board()

        except NoResultFound:
            raise BoardNotFound(f"Board with id {board_id} not found") from None

    async def get_unsolved_board(
        self, difficulty_level: DifficultyLevel, user: Optional[User] = None
    ) -> Board:
        try:
            difficulty_level_orm = await get_difficulty_level_orm(
                self, difficulty_level
            )

            stmt = (
                select(BoardORM)
                .join(BoardORM.difficulty_level)
                .where(BoardORM.difficulty_level_id == difficulty_level_orm.id)
                .options(selectinload(BoardORM.difficulty_level))
                .order_by(func.random())
                .limit(1)
            )

            if user is not None:
                stmt = stmt.outerjoin(
                    SingleplayerGameplayORM,
                    (SingleplayerGameplayORM.board_id == BoardORM.id)
                    & (SingleplayerGameplayORM.user_id == user.id),
                ).where(SingleplayerGameplayORM.id == None)

            result = await self.session.execute(stmt)
            return result.scalar_one().to_board()

        except NoResultFound:
            raise UnsolvedBoardNotFound(
                f"No unsolved board found for difficulty level {difficulty_level}"
            ) from None
