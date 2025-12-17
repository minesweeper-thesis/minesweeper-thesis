import uuid
from typing import Protocol


class OnlineUsersStore(Protocol):
    async def is_user_online(self, user_id: uuid.UUID) -> bool: ...
    async def set_user_online(self, user_id: uuid.UUID): ...
    async def set_user_offline(self, user_id: uuid.UUID): ...


def get_online_users_store() -> OnlineUsersStore:
    from .redis import RedisOnlineUsersStore

    return RedisOnlineUsersStore()
