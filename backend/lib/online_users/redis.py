import uuid

from backend.lib.redis_client import get_redis

from . import OnlineUsersStore


class RedisOnlineUsersStore(OnlineUsersStore):
    def __init__(self):
        self.key = "online_users"

    async def set_user_online(self, user_id: uuid.UUID) -> None:
        async for redis in get_redis():
            await redis.sadd(self.key, str(user_id))  # type: ignore

    async def set_user_offline(self, user_id: uuid.UUID) -> None:
        async for redis in get_redis():
            await redis.srem(self.key, str(user_id))  # type: ignore

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        async for redis in get_redis():
            return bool(await redis.sismember(self.key, str(user_id)))  # type: ignore

        return False
