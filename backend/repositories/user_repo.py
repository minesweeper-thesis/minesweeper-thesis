import uuid
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import case, func, select
from sqlalchemy.exc import NoResultFound

from backend.core.user import User
from backend.core.user.chat import UserChatMessage
from backend.db.db import DBSession
from backend.repositories import online_users
from backend.repositories.avatar import storage
from backend.repositories.helpers import get_users_transformer

from .exceptions import *
from .orm import *

OnlineUsersStore = Annotated[
    online_users.OnlineUsersStore, Depends(online_users.get_online_users_store)
]
AvatarStorage = Annotated[storage.AvatarStorage, Depends(storage.get_avatar_storage)]


class UserRepository:
    def __init__(
        self,
        session: DBSession,
        online_users_store: OnlineUsersStore,
        avatar_storage: AvatarStorage,
    ):
        self.session = session
        self.online_users_store = online_users_store
        self.avatar_storage = avatar_storage

    async def set_user_online(self, user_id: uuid.UUID):
        await self.online_users_store.set_user_online(user_id)

    async def set_user_offline(self, user_id: uuid.UUID):
        await self.online_users_store.set_user_offline(user_id)

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        return await self.online_users_store.is_user_online(user_id)

    async def get_user(self, user_id: uuid.UUID) -> User:
        try:
            stmt = select(UserORM).where(UserORM.id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one().to_user(await self.is_user_online(user_id))

        except NoResultFound:
            raise UserNotFound() from None

    async def set_avatar(self, user_id: uuid.UUID, content: bytes | None) -> User:
        if content:
            url = await self.avatar_storage.save(user_id, content)
        else:
            url = None

        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one()

        user.avatar_url = url
        await self.session.commit()
        await self.session.refresh(user)

        return user.to_user(await self.is_user_online(user_id))

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

    async def add_message(self, message: UserChatMessage):
        orm_message = UserChatMessageORM.from_chat_message(message)
        self.session.add(orm_message)
        await self.session.commit()

    async def get_messages(
        self, from_user_id: uuid.UUID, to_user_id: uuid.UUID, pagination_params: Params
    ) -> Page[UserChatMessage]:
        stmt = (
            select(UserChatMessageORM)
            .where(
                UserChatMessageORM.from_user_id == from_user_id,
                UserChatMessageORM.to_user_id == to_user_id,
            )
            .order_by(UserChatMessageORM.timestamp.desc())
        )

        async def async_transformer(items):
            messages = []
            for orm_message in items:
                orm_message: UserChatMessageORM
                from_user = await self.get_user(orm_message.from_user_id)
                to_user = await self.get_user(orm_message.to_user_id)
                message = UserChatMessage(
                    from_user=from_user,
                    to=to_user,
                    content=orm_message.content,
                    timestamp=orm_message.timestamp,
                )
                messages.append(message)
            return messages

        return await apaginate(
            self.session, stmt, pagination_params, transformer=async_transformer
        )
