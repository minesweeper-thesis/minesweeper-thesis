import uuid
from typing import Protocol

from backend.config import REDIS_URL


class OnlineUsersStore(Protocol):
    async def is_user_online(self, user_id: uuid.UUID) -> bool: ...
    async def set_user_online(self, user_id: uuid.UUID): ...
    async def set_user_offline(self, user_id: uuid.UUID): ...


def get_online_users_store() -> OnlineUsersStore:
    from .local import LocalOnlineUsersStore
    from .redis import RedisOnlineUsersStore

    if REDIS_URL:
        return RedisOnlineUsersStore()
    else:
        return LocalOnlineUsersStore()
