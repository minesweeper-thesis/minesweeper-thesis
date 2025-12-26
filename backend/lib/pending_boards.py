import logging
import uuid
from typing import Optional

from redis.asyncio import Redis

from backend.lib.redis_client import decode, encode

logger = logging.getLogger(__name__)

from backend import protocols
from backend.protocols.pending_boards import PendingBoard, PendingBoardMetadata


class RedisPendingStore(protocols.PendingBoardsStore):
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "pending_board:"

    async def create_pending(
        self, generation_id: uuid.UUID, metadata: PendingBoardMetadata
    ) -> PendingBoard:
        logger.debug(f"create_pending(generation_id={generation_id})")
        pending = PendingBoard(
            generation_id=generation_id,
            metadata=metadata,
        )
        data = encode(pending)

        async with self.redis.pipeline() as pipe:
            await pipe.set(f"{self.prefix}{generation_id}", data)

            if metadata.gameplay_id:
                await pipe.set(
                    f"{self.prefix}lookup:gameplay:{metadata.gameplay_id}",
                    encode(generation_id),
                )

            if metadata.session_id and metadata.round_index is not None:
                pipe.set(
                    f"{self.prefix}lookup:round:{metadata.session_id}:{metadata.round_index}",
                    encode(generation_id),
                )

            await pipe.execute()

        logger.debug(f"Created pending board {generation_id}")
        return pending

    async def mark_ready(self, generation_id: uuid.UUID, board_id: uuid.UUID) -> None:
        logger.debug(f"mark_ready(generation_id={generation_id}, board_id={board_id})")
        key = f"{self.prefix}{generation_id}"
        channel = f"{self.prefix}ready:{generation_id}"
        data = await self.redis.get(key)
        if data:
            pending = decode(data)
            pending.board_id = board_id

            await self.redis.set(key, encode(pending))
            await self.redis.publish(channel, "ready")
        logger.info(
            f"Pending board {generation_id} marked as ready with board_id {board_id}"
        )

    async def wait_for_ready(self, generation_id: uuid.UUID) -> Optional[PendingBoard]:
        logger.debug(f"wait_for_ready(generation_id={generation_id})")
        key = f"{self.prefix}{generation_id}"
        channel = f"{self.prefix}ready:{generation_id}"

        data = await self.redis.get(key)
        if not data:
            return None

        pending = decode(data)
        if pending.board_id:
            return pending

        pubsub = self.redis.pubsub()
        try:
            await pubsub.subscribe(channel)

            async def wait():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        data = await self.redis.get(key)
                        return decode(data) if data else None

            result = await wait()
            return result
        finally:
            await pubsub.aclose()

    async def get_pending_gameplay(self, id: uuid.UUID) -> Optional[PendingBoard]:
        logger.debug(f"get_pending_gameplay(id={id})")
        gen_id_bytes = await self.redis.get(f"{self.prefix}lookup:gameplay:{id}")
        if gen_id_bytes:
            gen_id_str = decode(gen_id_bytes)
            data = await self.redis.get(f"{self.prefix}{gen_id_str}")
            if data:
                return decode(data)
        return None

    async def get_pending_round(
        self, session_id: uuid.UUID, round_index: int
    ) -> Optional[PendingBoard]:
        logger.debug(
            f"get_pending_round(session_id={session_id}, round_index={round_index})"
        )
        gen_id_bytes = await self.redis.get(
            f"{self.prefix}lookup:round:{session_id}:{round_index}"
        )
        if gen_id_bytes:
            gen_id_str = decode(gen_id_bytes)
            data = await self.redis.get(f"{self.prefix}{gen_id_str}")
            if data:
                return decode(data)
        return None


__all__ = ["RedisPendingStore"]
