import uuid

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select

from backend.db.db import DBSession
from backend.models.game_models import SingleplayerGameplay

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
            SingleplayerGameplay.user_id == user_id
        )
        return await apaginate(self.session, stmt, pagination_params)
