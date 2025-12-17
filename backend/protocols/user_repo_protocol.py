import uuid
from typing import Protocol

from fastapi_pagination import Page, Params

from backend.core.user import User, UserChatMessage


class UserRepository(Protocol):
    async def set_user_online(self, user_id: uuid.UUID) -> None: ...

    async def set_user_offline(self, user_id: uuid.UUID) -> None: ...

    async def is_user_online(self, user_id: uuid.UUID) -> bool: ...

    async def get_user(self, user_id: uuid.UUID) -> User: ...

    async def set_avatar(self, user_id: uuid.UUID, content: bytes | None) -> User: ...

    async def search_users(self, query: str, params: Params) -> Page[User]: ...

    async def add_message(self, message: UserChatMessage) -> None: ...

    async def get_messages(
        self, from_user_id: uuid.UUID, to_user_id: uuid.UUID, pagination_params: Params
    ): ...


__all__ = ["UserRepository"]
