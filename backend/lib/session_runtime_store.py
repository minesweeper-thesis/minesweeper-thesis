import uuid
from datetime import datetime
from typing import Optional

from redis.asyncio import Redis

from backend.lib.redis_client import decode, encode
from backend.protocols.session_runtime_store_protocol import SessionRuntimeStore


class RedisSessionRuntimeStore(SessionRuntimeStore):
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "session_runtime:"

    async def set_countdown(
        self, session_id: uuid.UUID, countdown_to: datetime, start_at: datetime
    ) -> None:
        key = f"{self.prefix}{session_id}:countdown"
        data = {
            "countdown_to": countdown_to,
            "start_at": start_at,
        }
        await self.redis.set(key, encode(data))

    async def get_countdown(
        self, session_id: uuid.UUID
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        key = f"{self.prefix}{session_id}:countdown"
        data = await self.redis.get(key)
        if not data:
            return None, None

        decoded = decode(data)
        return decoded["countdown_to"], decoded["start_at"]

    async def clear_countdown(self, session_id: uuid.UUID) -> None:
        key = f"{self.prefix}{session_id}:countdown"
        await self.redis.delete(key)
