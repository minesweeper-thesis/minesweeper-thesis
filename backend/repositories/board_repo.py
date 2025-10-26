from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import func

from backend.models.board_models import *
from backend.models.game_models import SingleplayerGameplay
from backend.models.user_models import User
from backend.schemas.board_schemas import DifficultyLevel

from ..db import get_async_session
from .exceptions import *


class BoardRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_async_session)]):
        self.session = session

    async def add_board(self, board: Board) -> Board:
        self.session.add(board)
        await self.session.commit()
        await self.session.refresh(board, attribute_names=["board_type"])
        return board

    async def get_board_type(
        self, rows: int, columns: int, mine_count: int
    ) -> BoardType:
        stmt = select(BoardType).where(
            BoardType.rows == rows,
            BoardType.columns == columns,
            BoardType.mine_count == mine_count,
        )
        result = await self.session.execute(stmt)
        board_type = result.scalar_one_or_none()

        if board_type is None:
            board_type = BoardType(rows=rows, columns=columns, mine_count=mine_count)
            self.session.add(board_type)
            await self.session.commit()
            await self.session.refresh(board_type)

        return board_type

    async def get_board_by_id(self, board_id: uuid.UUID) -> Board:
        try:
            stmt = (
                select(Board)
                .where(Board.id == board_id)
                .options(selectinload(Board.board_type))
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()
        except NoResultFound:
            raise BoardNotFound(f"Board with id {board_id} not found") from None

    async def get_unsolved_board(
        self, difficulty_level: DifficultyLevel, user: Optional[User] = None
    ) -> Board:
        try:
            board_type = await self.get_board_type(**difficulty_level.model_dump())

            stmt = (
                select(Board)
                .join(Board.board_type)
                .where(Board.board_type_id == board_type.id)
                .options(selectinload(Board.board_type))
                .order_by(func.random())
                .limit(1)
            )

            if user is not None:
                stmt = stmt.outerjoin(
                    SingleplayerGameplay,
                    (SingleplayerGameplay.board_id == Board.id)
                    & (SingleplayerGameplay.user_id == user.id),
                ).where(SingleplayerGameplay.id == None)

            result = await self.session.execute(stmt)
            return result.scalar_one()
        except NoResultFound:
            raise UnsolvedBoardNotFound(
                f"No unsolved board found for difficulty level {difficulty_level}"
            ) from None
