import uuid
from typing import Optional

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from backend.db.db import DBSession
from backend.models.game_models import *

from .exceptions import *


class GameRepository:
    def __init__(self, session: DBSession):
        self.session = session

    async def add_gameplay(self, gameplay: SingleplayerGameplay):
        self.session.add(gameplay)
        await self.session.commit()
        await self.session.refresh(gameplay)
        return gameplay

    async def get_gameplays(self, user_id: uuid.UUID, pagination_params: Params):
        stmt = select(SingleplayerGameplay).where(
            SingleplayerGameplay.user_id == user_id,
        )
        return await apaginate(self.session, stmt, pagination_params)

    async def get_gameplay_by_id(self, gameplay_id: uuid.UUID) -> SingleplayerGameplay:
        try:
            stmt = select(SingleplayerGameplay).where(
                SingleplayerGameplay.id == gameplay_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()

        except NoResultFound:
            raise GameplayNotFound() from None

    async def update_gameplay(
        self,
        gameplay_id: uuid.UUID,
        status: Optional[GameStatus] = None,
        result: Optional[GameResult] = None,
        time: Optional[float] = None,
        used_prompts: Optional[bool] = None,
        revealed_cells: Optional[list[tuple[int, int]]] = None,
    ) -> SingleplayerGameplay:
        gameplay = await self.get_gameplay_by_id(gameplay_id)

        if status is not None:
            gameplay.status = status
        if result is not None:
            gameplay.result = result
        if time is not None:
            gameplay.time = time
        if used_prompts is not None:
            gameplay.used_hints = used_prompts
        if revealed_cells is not None:
            gameplay.revealed_cells = revealed_cells

        await self.session.commit()
        await self.session.refresh(gameplay)
        return gameplay
