import logging
import uuid

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import case, func, select
from sqlalchemy.exc import NoResultFound

logger = logging.getLogger(__name__)

from backend import protocols
from backend.core.user import User
from backend.core.user.chat import UserChatMessage
from backend.db.db import DBSession
from backend.lib.avatar.storage import get_avatar_storage
from backend.lib.online_users import get_online_users_store
from backend.repositories.helpers import get_users_transformer

from .exceptions import *
from .orm import *


class UserRepository(protocols.UserRepository):
    def __init__(self, session: DBSession):
        self.session = session
        self.online_users_store = get_online_users_store()
        self.avatar_storage = get_avatar_storage()

    async def set_user_online(self, user_id: uuid.UUID):
        logger.debug(f"set_user_online(user_id={user_id})")
        await self.online_users_store.set_user_online(user_id)

    async def set_user_offline(self, user_id: uuid.UUID):
        logger.debug(f"set_user_offline(user_id={user_id})")
        await self.online_users_store.set_user_offline(user_id)

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        logger.debug(f"is_user_online(user_id={user_id})")
        return await self.online_users_store.is_user_online(user_id)

    async def get_user(self, user_id: uuid.UUID) -> User:
        logger.debug(f"get_user(user_id={user_id})")
        try:
            stmt = select(UserORM).where(UserORM.id == user_id)
            result = await self.session.execute(stmt)
            user = result.scalar_one().to_user(await self.is_user_online(user_id))
            logger.debug(f"Retrieved user {user_id}")
            return user

        except NoResultFound:
            logger.warning(f"User {user_id} not found")
            raise UserNotFound() from None

    async def set_avatar(self, user_id: uuid.UUID, content: bytes | None) -> User:
        logger.debug(
            f"set_avatar(user_id={user_id}, content_size={len(content) if content else 0})"
        )
        if content:
            url = await self.avatar_storage.save(user_id, content)
            logger.info(f"Avatar saved for user {user_id}: {url}")
        else:
            url = None
            logger.info(f"Avatar removed for user {user_id}")

        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one()

        user.avatar_url = url
        await self.session.commit()
        await self.session.refresh(user)

        return user.to_user(await self.is_user_online(user_id))

    async def search_users(self, query: str, params):
        logger.debug(f"Searching users with query: '{query}'")
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
        logger.debug(f"add_message(from={message.from_user.id}, to={message.to.id})")
        orm_message = UserChatMessageORM.from_chat_message(message)
        self.session.add(orm_message)
        await self.session.commit()

    async def get_messages(
        self, from_user_id: uuid.UUID, to_user_id: uuid.UUID, pagination_params: Params
    ):
        logger.debug(
            f"get_messages(from_user_id={from_user_id}, to_user_id={to_user_id})"
        )
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
