import uuid
from typing import Optional

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

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
        stmt = (
            select(SingleplayerGameplayORM)
            .options(
                selectinload(SingleplayerGameplayORM.board).selectinload(
                    BoardORM.difficulty_level
                ),
                selectinload(SingleplayerGameplayORM.user),
            )
            .where(
                SingleplayerGameplayORM.user_id == user_id,
            )
        )
        res = await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=lambda items: [item.to_gameplay() for item in items],
        )
        print(res)
        return res

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
        self, gameplay: SingleplayerGameplay
    ) -> SingleplayerGameplay:
        existing = await self._get_gameplay_orm(gameplay.id)
        user_id = existing.user_id
        self.session.expunge(existing)

        updated_orm = SingleplayerGameplayORM.from_gameplay(
            gameplay, gameplay.board.id, user_id
        )
        await self.session.merge(updated_orm)
        await self.session.commit()
        return gameplay
