import uuid
from typing import Optional

from redis.asyncio import Redis

from backend.lib.redis_client import decode, encode
from backend.protocols.scheduler_protocol import JobID
from backend.protocols.session_runtime_store_protocol import SessionRuntimeStore
from backend.services.dto import RoundSchedule


class RedisSessionRuntimeStore(SessionRuntimeStore):
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "session_runtime:"

    async def set_round_schedule(
        self,
        session_id: uuid.UUID,
        round_schedule: RoundSchedule,
    ) -> None:
        key = f"{self.prefix}{session_id}:schedule"
        await self.redis.set(key, encode(round_schedule))

    async def get_round_schedule(
        self, session_id: uuid.UUID
    ) -> Optional[RoundSchedule]:
        key = f"{self.prefix}{session_id}:schedule"
        data = await self.redis.get(key)
        if not data:
            return None
        return decode(data)

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

    async def set_lock_job_id(
        self, session_id: uuid.UUID, job_id: JobID | None
    ) -> None:
        key = f"{self.prefix}{session_id}:lock_job"
        if job_id is None:
            await self.redis.delete(key)
        else:
            await self.redis.set(key, encode(job_id))

    async def get_lock_job_id(self, session_id: uuid.UUID) -> Optional[JobID]:
        key = f"{self.prefix}{session_id}:lock_job"
        data = await self.redis.get(key)
        if not data:
            return None
        return decode(data)
