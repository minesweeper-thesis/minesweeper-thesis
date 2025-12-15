import asyncio
import logging
import pickle
import time
import uuid
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

from backend import protocols
from backend.protocols.pending_boards import PendingBoard, PendingBoardMetadata


class RedisPendingStore(protocols.PendingBoardsStore):
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "pending_board:"

    async def create_pending(
        self,
        generation_id: uuid.UUID,
        metadata: PendingBoardMetadata,
        ttl_seconds: int,
    ) -> PendingBoard:
        logger.debug(
            f"create_pending(generation_id={generation_id}, ttl_seconds={ttl_seconds})"
        )
        pending = PendingBoard(
            generation_id=generation_id,
            metadata=metadata,
        )
        data = pickle.dumps(pending)

        async with self.redis.pipeline() as pipe:
            await pipe.set(f"{self.prefix}{generation_id}", data, ex=ttl_seconds)

            if metadata.gameplay_id:
                await pipe.set(
                    f"{self.prefix}lookup:gameplay:{metadata.gameplay_id}",
                    str(generation_id),
                    ex=ttl_seconds,
                )

            if metadata.session_id and metadata.round_index is not None:
                pipe.set(
                    f"{self.prefix}lookup:round:{metadata.session_id}:{metadata.round_index}",
                    str(generation_id),
                    ex=ttl_seconds,
                )

            await pipe.execute()

        logger.debug(f"Created pending board {generation_id} with TTL {ttl_seconds}s")
        return pending

    async def mark_ready(self, generation_id: uuid.UUID, board_id: uuid.UUID) -> None:
        logger.debug(f"mark_ready(generation_id={generation_id}, board_id={board_id})")
        key = f"{self.prefix}{generation_id}"
        data = await self.redis.get(key)
        if data:
            pending = pickle.loads(data)
            pending.board_id = board_id

            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.set(key, pickle.dumps(pending), ex=ttl)
        logger.info(
            f"Pending board {generation_id} marked as ready with board_id {board_id}"
        )

    async def wait_for_ready(
        self, generation_id: uuid.UUID, timeout: float | None = None
    ) -> Optional[PendingBoard]:
        logger.debug(
            f"wait_for_ready(generation_id={generation_id}, timeout={timeout})"
        )
        start_time = time.time()
        key = f"{self.prefix}{generation_id}"

        while True:
            data = await self.redis.get(key)
            if not data:
                return None

            pending = pickle.loads(data)
            if pending.board_id:
                return pending

            if timeout is not None and (time.time() - start_time) >= timeout:
                return None

            await asyncio.sleep(0.1)

    async def get_pending_gameplay(self, id: uuid.UUID) -> Optional[PendingBoard]:
        logger.debug(f"get_pending_gameplay(id={id})")
        gen_id_str = await self.redis.get(f"{self.prefix}lookup:gameplay:{id}")
        if gen_id_str:
            data = await self.redis.get(f"{self.prefix}{gen_id_str}")
            if data:
                return pickle.loads(data)
        return None

    async def get_pending_round(
        self, session_id: uuid.UUID, round_index: int
    ) -> Optional[PendingBoard]:
        logger.debug(
            f"get_pending_round(session_id={session_id}, round_index={round_index})"
        )
        gen_id_str = await self.redis.get(
            f"{self.prefix}lookup:round:{session_id}:{round_index}"
        )
        if gen_id_str:
            data = await self.redis.get(f"{self.prefix}{gen_id_str}")
            if data:
                return pickle.loads(data)
        return None


__all__ = ["RedisPendingStore"]
