import uuid
from typing import Optional

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from backend.core.game import GameResult, GameStatus
from backend.core.singleplayer import SingleplayerGameplay
from backend.db.db import DBSession

from .exceptions import *
from .orm import *


class SingleplayerRepository:
    def __init__(self, session: DBSession):
        self.session = session

    async def add_gameplay(
        self,
        gameplay: SingleplayerGameplay,
        board_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> None:
        orm = SingleplayerGameplayORM.from_gameplay(gameplay, board_id, user_id)
        self.session.add(orm)
        await self.session.commit()

    async def get_gameplays(self, user_id: uuid.UUID, pagination_params: Params):
        stmt = select(SingleplayerGameplayORM).where(
            SingleplayerGameplayORM.user_id == user_id,
        )
        return await apaginate(self.session, stmt, pagination_params)

    async def _get_gameplay_orm(
        self, gameplay_id: uuid.UUID
    ) -> SingleplayerGameplayORM:
        try:
            stmt = (
                select(SingleplayerGameplayORM)
                .options(
                    selectinload(SingleplayerGameplayORM.board).selectinload(
                        BoardORM.difficulty_level
                    ),
                    selectinload(SingleplayerGameplayORM.user),
                )
                .where(SingleplayerGameplayORM.id == gameplay_id)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()

        except NoResultFound:
            raise GameplayNotFound() from None

    async def get_gameplay_by_id(self, gameplay_id: uuid.UUID) -> SingleplayerGameplay:
        return (await self._get_gameplay_orm(gameplay_id)).to_gameplay()

    async def update_gameplay(
        self,
        gameplay_id: uuid.UUID,
        status: Optional[GameStatus] = None,
        result: Optional[GameResult] = None,
        time: Optional[float] = None,
        used_prompts: Optional[bool] = None,
        revealed_cells: Optional[list[tuple[int, int]]] = None,
    ) -> SingleplayerGameplayORM:
        gameplay = await self._get_gameplay_orm(gameplay_id)

        if status is not None:
            gameplay.status = GameStatusEnum(status)
        if result is not None:
            gameplay.result = GameResultEnum(result)
        if time is not None:
            gameplay.time = time
        if used_prompts is not None:
            gameplay.used_hints = used_prompts
        if revealed_cells is not None:
            gameplay.revealed_cells = revealed_cells

        await self.session.commit()
        await self.session.refresh(gameplay)
        return gameplay
