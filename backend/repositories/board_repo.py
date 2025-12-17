import logging
import uuid
from dataclasses import asdict
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import func

logger = logging.getLogger(__name__)

from backend import protocols
from backend.core.board import Board, DifficultyLevel, GenerationSettings, Minefields
from backend.db import DBSession

from .exceptions import *
from .orm import *


class BoardRepository(protocols.BoardRepository):
    def __init__(self, session: DBSession):
        self.session = session

    async def add_board(self, board: Board) -> None:
        logger.debug(
            f"add_board(board_id={board.id}, difficulty={board.difficulty_level.rows}x{board.difficulty_level.columns})"
        )
        difficulty_level_orm = await self.get_difficulty_level_orm(
            board.difficulty_level
        )
        board_orm = BoardORM.from_board(board, difficulty_level_orm.id)

        self.session.add(board_orm)
        await self.session.commit()
        logger.info(
            f"Board {board.id} added with difficulty {board.difficulty_level.rows}x{board.difficulty_level.columns}"
        )

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

    async def get_board_by_id(self, board_id: uuid.UUID) -> Board:
        logger.debug(f"get_board_by_id(board_id={board_id})")
        try:
            stmt = (
                select(BoardORM)
                .where(BoardORM.id == board_id)
                .options(selectinload(BoardORM.difficulty_level))
            )
            result = await self.session.execute(stmt)
            board = result.scalar_one().to_board()
            logger.debug(f"Retrieved board {board_id}")
            return board

        except NoResultFound:
            logger.warning(f"Board {board_id} not found")
            raise BoardNotFound(f"Board with id {board_id} not found") from None

    async def get_board(
        self,
        difficulty_level: Optional[DifficultyLevel] = None,
        minefields: Optional[Minefields] = None,
        generation_settings: Optional[GenerationSettings] = None,
    ) -> Board:
        logger.debug(
            f"get_board(difficulty_level={difficulty_level}, has_minefields={minefields is not None}, has_settings={generation_settings is not None})"
        )
        try:
            args = []

            if difficulty_level is not None:
                difficulty_level_orm = await self.get_difficulty_level_orm(
                    difficulty_level
                )
                args.append(BoardORM.difficulty_level_id == difficulty_level_orm.id)

            if minefields is not None:
                normalized = [list(coord) for coord in minefields]
                args.append(BoardORM.minefields == normalized)

            if generation_settings is not None:
                args.append(BoardORM.generation_settings == asdict(generation_settings))

            stmt = (
                select(BoardORM)
                .options(selectinload(BoardORM.difficulty_level))
                .where(*args)
            )

            result = await self.session.execute(stmt)
            return result.scalar_one().to_board()

        except NoResultFound:
            raise BoardNotFound(
                "Board with specified difficulty level and minefields not found"
            ) from None

    async def get_unsolved_board(
        self,
        difficulty_level: DifficultyLevel,
        *,
        generation_settings: Optional[GenerationSettings] = None,
        user_id: Optional[uuid.UUID] = None,
        user_ids: list[uuid.UUID] = None,  # type: ignore
    ) -> Board:
        if user_ids is None:
            user_ids = []

        if user_id:
            user_ids.append(user_id)

        difficulty_level_orm = await self.get_difficulty_level_orm(difficulty_level)

        args = [BoardORM.difficulty_level_id == difficulty_level_orm.id]
        if generation_settings is not None:
            args.append(BoardORM.generation_settings == asdict(generation_settings))

        try:
            stmt = (
                select(BoardORM)
                .join(BoardORM.difficulty_level)
                .where(*args)
                .options(selectinload(BoardORM.difficulty_level))
                .order_by(func.random())
                .limit(1)
            )

            if user_ids:
                stmt = stmt.outerjoin(
                    SingleplayerGameplayORM,
                    (SingleplayerGameplayORM.board_id == BoardORM.id)
                    & (SingleplayerGameplayORM.user_id.in_(user_ids)),
                ).where(SingleplayerGameplayORM.id == None)

                stmt = (
                    stmt.outerjoin(
                        MultiplayerRoundORM, MultiplayerRoundORM.board_id == BoardORM.id
                    )
                    .outerjoin(
                        MultiplayerGameplayORM,
                        (
                            MultiplayerGameplayORM.session_id
                            == MultiplayerRoundORM.session_id
                        )
                        & (
                            MultiplayerGameplayORM.round_index
                            == MultiplayerRoundORM.round_index
                        )
                        & (MultiplayerGameplayORM.user_id.in_(user_ids)),
                    )
                    .where(MultiplayerGameplayORM.user_id == None)
                )

            result = await self.session.execute(stmt)
            return result.scalar_one().to_board()

        except NoResultFound:
            raise UnsolvedBoardNotFound(
                f"No unsolved board found for difficulty level {difficulty_level}"
            ) from None
