import uuid

from backend.lib.redis_client import encode, get_redis_client

from . import OnlineUsersStore


class RedisOnlineUsersStore(OnlineUsersStore):
    def __init__(self):
        self.key = "online_users"

    async def set_user_online(self, user_id: uuid.UUID) -> None:
        redis = await get_redis_client()
        await redis.sadd(self.key, encode(user_id))  # type: ignore

    async def set_user_offline(self, user_id: uuid.UUID) -> None:
        redis = await get_redis_client()
        await redis.srem(self.key, encode(user_id))  # type: ignore

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        redis = await get_redis_client()
        result = await redis.sismember(self.key, encode(user_id))  # type: ignore
        return bool(result)  # type: ignore
