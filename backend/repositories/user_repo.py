import uuid

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from backend.core.user import User
from backend.db.db import DBSession

from .exceptions import *
from .orm import *


class UserRepository:
    def __init__(self, session: DBSession):
        self.session = session

    async def get_user(self, user_id: uuid.UUID) -> User:
        try:
            stmt = select(UserORM).where(UserORM.id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one().to_user()

        except NoResultFound:
            raise UserNotFound() from None

    async def set_avatar_url(self, user_id: uuid.UUID, url: str | None):
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one()

        user.avatar_url = url
        await self.session.commit()
        await self.session.refresh(user)
