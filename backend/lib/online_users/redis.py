import uuid

from backend.lib.redis_client import get_redis_client

from . import OnlineUsersStore


class RedisOnlineUsersStore(OnlineUsersStore):
    def __init__(self):
        self.key = "online_users"

    async def set_user_online(self, user_id: uuid.UUID) -> None:
        redis = await get_redis_client()
        await redis.sadd(self.key, str(user_id))  # type: ignore

    async def set_user_offline(self, user_id: uuid.UUID) -> None:
        redis = await get_redis_client()
        await redis.srem(self.key, str(user_id))  # type: ignore

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        redis = await get_redis_client()
        return bool(await redis.sismember(self.key, str(user_id)))  # type: ignore
