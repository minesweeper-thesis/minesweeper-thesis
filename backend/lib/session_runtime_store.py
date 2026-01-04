import logging
import uuid
from typing import Optional

from redis.asyncio import Redis

from backend.lib.redis_client import decode, encode
from backend.protocols.scheduler_protocol import JobID
from backend.protocols.session_runtime_store_protocol import SessionRuntimeStore
from backend.services.dto import RoundSchedule

logger = logging.getLogger(__name__)


class RedisSessionRuntimeStore(SessionRuntimeStore):
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "session_runtime:"

    async def set_round_schedule(
        self,
        session_id: uuid.UUID,
        round_schedule: RoundSchedule,
        ttl: int,
    ) -> None:
        logger.debug(
            f"set_round_schedule(session_id={session_id}, round_schedule={round_schedule}, ttl={ttl})"
        )
        key = f"{self.prefix}{session_id}:schedule"
        await self.redis.set(key, encode(round_schedule), ex=ttl)

    async def get_round_schedule(
        self, session_id: uuid.UUID
    ) -> Optional[RoundSchedule]:
        logger.debug(f"get_round_schedule(session_id={session_id})")
        key = f"{self.prefix}{session_id}:schedule"
        data = await self.redis.get(key)
        if not data:
            return None
        return decode(data)

    async def delete_round_schedule(self, session_id: uuid.UUID) -> None:
        logger.debug(f"delete_round_schedule(session_id={session_id})")
        key = f"{self.prefix}{session_id}:schedule"
        await self.redis.delete(key)

    async def get_ready_board(self, session_id: uuid.UUID) -> Optional[uuid.UUID]:
        logger.debug(f"get_ready_board(session_id={session_id})")
        key = f"{self.prefix}{session_id}:ready_boards"
        data = await self.redis.lpop(key)  # type: ignore[misc]
        if data:
            return decode(data)  # type: ignore[misc]
        return None

    async def peek_ready_board(self, session_id: uuid.UUID) -> Optional[uuid.UUID]:
        logger.debug(f"peek_ready_board(session_id={session_id})")
        key = f"{self.prefix}{session_id}:ready_boards"
        data = await self.redis.lindex(key, 0)  # type: ignore[misc]
        if data:
            return decode(data)  # type: ignore[misc]
        return None

    async def wait_for_board_ready(self, session_id: uuid.UUID) -> None:
        logger.debug(f"wait_for_board(session_id={session_id})")
        await self._set_waiting_for_round(session_id, True)
        channel = f"{self.prefix}{session_id}:ready"

        if await self.is_board_ready(session_id):
            await self._set_waiting_for_round(session_id, False)
            return

        pubsub = self.redis.pubsub()
        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    return

            raise RuntimeError("pub/sub listener exited unexpectedly")
        finally:
            await pubsub.aclose()
            await self._set_waiting_for_round(session_id, False)

    async def add_ready_board(self, session_id: uuid.UUID, board_id: uuid.UUID) -> None:
        logger.debug(f"add_ready_board(session_id={session_id}, board_id={board_id})")
        key = f"{self.prefix}{session_id}:ready_boards"
        await self.redis.rpush(key, encode(board_id))  # type: ignore[misc]

        channel = f"{self.prefix}{session_id}:ready"
        await self.redis.publish(channel, "ready")

    async def is_board_ready(self, session_id: uuid.UUID) -> bool:
        logger.debug(f"is_board_ready(session_id={session_id})")
        key = f"{self.prefix}{session_id}:ready_boards"
        length = await self.redis.llen(key)  # type: ignore[misc]
        return length > 0

    async def add_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None:
        logger.debug(
            f"add_generation(session_id={session_id}, generation_id={generation_id})"
        )
        key = f"{self.prefix}{session_id}:generating"
        await self.redis.sadd(key, encode(generation_id))  # type: ignore[misc]

    async def remove_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None:
        logger.debug(
            f"remove_generation(session_id={session_id}, generation_id={generation_id})"
        )
        key = f"{self.prefix}{session_id}:generating"
        await self.redis.srem(key, encode(generation_id))  # type: ignore[misc]

    async def is_generating(self, session_id: uuid.UUID) -> bool:
        logger.debug(f"is_generating(session_id={session_id})")
        key = f"{self.prefix}{session_id}:generating"
        count = await self.redis.scard(key)  # type: ignore[misc]
        return count > 0

    async def set_lock_job_id(
        self, session_id: uuid.UUID, job_id: JobID | None
    ) -> None:
        logger.debug(f"set_lock_job_id(session_id={session_id}, job_id={job_id})")
        key = f"{self.prefix}{session_id}:lock_job"
        if job_id is None:
            await self.redis.delete(key)
        else:
            await self.redis.set(key, encode(job_id))

    async def get_lock_job_id(self, session_id: uuid.UUID) -> Optional[JobID]:
        logger.debug(f"get_lock_job_id(session_id={session_id})")
        key = f"{self.prefix}{session_id}:lock_job"
        data = await self.redis.get(key)
        if not data:
            return None
        return decode(data)

    async def _set_waiting_for_round(
        self, session_id: uuid.UUID, waiting: bool
    ) -> None:
        logger.debug(
            f"_set_waiting_for_round(session_id={session_id}, waiting={waiting})"
        )
        key = f"{self.prefix}{session_id}:waiting_for_round"
        if waiting:
            await self.redis.set(key, encode(waiting))
        else:
            await self.redis.delete(key)

    async def is_waiting_for_round(self, session_id: uuid.UUID) -> bool:
        logger.debug(f"is_waiting_for_round(session_id={session_id})")
        key = f"{self.prefix}{session_id}:waiting_for_round"
        data = await self.redis.get(key)
        if not data:
            return False
        return decode(data)
