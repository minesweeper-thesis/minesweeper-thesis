import uuid

from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import case, func, select
from sqlalchemy.exc import NoResultFound

from backend.core.user import User
from backend.db.db import DBSession
from backend.repositories.helpers import get_users_transformer

from .exceptions import *
from .orm import *


class UserRepository:
    online_users: set[uuid.UUID] = set()

    def __init__(self, session: DBSession):
        self.session = session

    async def set_user_online(self, user_id: uuid.UUID):
        self.online_users.add(user_id)

    async def set_user_offline(self, user_id: uuid.UUID):
        self.online_users.discard(user_id)

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        return user_id in self.online_users

    async def get_user(self, user_id: uuid.UUID) -> User:
        try:
            stmt = select(UserORM).where(UserORM.id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one().to_user(await self.is_user_online(user_id))

        except NoResultFound:
            raise UserNotFound() from None

    async def set_avatar_url(self, user_id: uuid.UUID, url: str | None):
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one()

        user.avatar_url = url
        await self.session.commit()
        await self.session.refresh(user)

    async def search_users(self, query: str, params):
        priority = case(
            (UserORM.nickname.ilike(f"{query}%"), 1),
            (UserORM.email.ilike(f"{query}%"), 2),  # type: ignore
            (UserORM.nickname.ilike(f"%{query}%"), 3),
            (UserORM.email.ilike(f"%{query}%"), 4),  # type: ignore
            else_=5,
        )

        stmt = (
            select(UserORM)
            .where(
                UserORM.nickname.ilike(f"%{query}%")
                | UserORM.email.ilike(f"%{query}%")  # type: ignore
            )
            .order_by(
                priority,
                func.length(UserORM.nickname),
                UserORM.nickname,
                func.length(UserORM.email),
                UserORM.email,
            )
        )

        return await apaginate(
            self.session,
            stmt,
            params,
            transformer=get_users_transformer(self),
        )
