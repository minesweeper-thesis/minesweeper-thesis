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

    async def set_round_schedule(
        self,
        session_id: uuid.UUID,
        countdown_to: datetime,
        start_at: datetime,
        end_at: datetime,
    ) -> None:
        key = f"{self.prefix}{session_id}:schedule"
        data = {
            "countdown_to": countdown_to,
            "start_at": start_at,
            "end_at": end_at,
        }
        await self.redis.set(key, encode(data))

    async def get_round_schedule(
        self, session_id: uuid.UUID
    ) -> tuple[Optional[datetime], Optional[datetime], Optional[datetime]]:
        key = f"{self.prefix}{session_id}:schedule"
        data = await self.redis.get(key)
        if not data:
            return None, None, None
        decoded = decode(data)
        return decoded["countdown_to"], decoded["start_at"], decoded["end_at"]

    async def delete_round_schedule(self, session_id: uuid.UUID) -> None:
        key = f"{self.prefix}{session_id}:schedule"
        await self.redis.delete(key)

    async def wait_for_next_round(self, session_id: uuid.UUID) -> None:
        channel = f"{self.prefix}{session_id}:ready"

        pubsub = self.redis.pubsub()
        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    return
        finally:
            await pubsub.aclose()

    async def notify_round_ready(self, session_id: uuid.UUID) -> None:
        channel = f"{self.prefix}{session_id}:ready"
        await self.redis.publish(channel, "ready")

    async def add_pending_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None:
        key = f"{self.prefix}{session_id}:generating"
        await self.redis.sadd(key, encode(generation_id))  # type: ignore[misc]

    async def remove_pending_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None:
        key = f"{self.prefix}{session_id}:generating"
        await self.redis.srem(key, encode(generation_id))  # type: ignore[misc]

    async def is_generating(self, session_id: uuid.UUID) -> bool:
        key = f"{self.prefix}{session_id}:generating"
        count = await self.redis.scard(key)  # type: ignore[misc]
        return count > 0
