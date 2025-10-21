from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.board import *

from ..db import get_async_session
from .exceptions import *


class BoardRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_async_session)]):
        self.session = session

    async def add_board(self, board: Board):
        self.session.add(board)
        await self.session.commit()
        await self.session.refresh(board)
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
