import uuid
from typing import Protocol

from .local import LocalOnlineUsersStore


class OnlineUsersStore(Protocol):
    async def is_user_online(self, user_id: uuid.UUID) -> bool: ...
    async def set_user_online(self, user_id: uuid.UUID): ...
    async def set_user_offline(self, user_id: uuid.UUID): ...


_online_users_store = LocalOnlineUsersStore()


def get_online_users_store() -> OnlineUsersStore:
    return _online_users_store
