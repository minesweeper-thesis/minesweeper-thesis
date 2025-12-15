import asyncio
import logging
import pickle
import time
import uuid
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

from backend.config import REDIS_URL
from backend.lib.redis_client import redis_client
from backend.protocols.pending_boards import PendingBoard, PendingBoardMetadata
from backend.protocols.pending_boards_store_protocol import PendingBoardsStore


class InMemoryPendingStore(PendingBoardsStore):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, PendingBoard] = {}
        self._expires_at: dict[uuid.UUID, float] = {}
        self._ready: dict[uuid.UUID, bool] = {}

    def _now(self) -> float:
        return time.time()

    def _is_expired(self, gameplay_id: uuid.UUID) -> bool:
        exp = self._expires_at.get(gameplay_id)
        return exp is None or self._now() >= exp

    async def create_pending(
        self,
        generation_id: uuid.UUID,
        metadata: PendingBoardMetadata,
        ttl_seconds: int,
    ) -> PendingBoard:
        logger.debug(
            f"create_pending(generation_id={generation_id}, ttl_seconds={ttl_seconds})"
        )
        await self._clear_expired()
        now = self._now()
        pending = PendingBoard(
            generation_id=generation_id,
            metadata=metadata,
        )

        self._store[generation_id] = pending
        self._expires_at[generation_id] = now + ttl_seconds
        self._ready[generation_id] = False

        logger.debug(f"Created pending board {generation_id} with TTL {ttl_seconds}s")
        return pending

    async def mark_ready(self, generation_id: uuid.UUID, board_id: uuid.UUID) -> None:
        logger.debug(f"mark_ready(generation_id={generation_id}, board_id={board_id})")
        await self._clear_expired()
        self._ready[generation_id] = True
        if generation_id in self._store:
            self._store[generation_id].board_id = board_id
        logger.info(
            f"Pending board {generation_id} marked as ready with board_id {board_id}"
        )

    async def wait_for_ready(
        self, generation_id: uuid.UUID, timeout: float | None = None
    ) -> Optional[PendingBoard]:
        logger.debug(
            f"wait_for_ready(generation_id={generation_id}, timeout={timeout})"
        )
        if self._ready.get(generation_id, False):
            return self._store[generation_id]

        start_time = self._now()
        while True:
            await asyncio.sleep(0.1)
            if self._ready.get(generation_id, False):
                return self._store[generation_id]

            if timeout is not None and (self._now() - start_time) >= timeout:
                return None

    async def get_pending_gameplay(self, id: uuid.UUID) -> Optional[PendingBoard]:
        logger.debug(f"get_pending_gameplay(id={id})")
        await self._clear_expired()

        for pending in self._store.values():
            if pending.metadata.gameplay_id == id:
                return pending
        return None

    async def get_pending_round(
        self, session_id: uuid.UUID, round_index: int
    ) -> Optional[PendingBoard]:
        logger.debug(
            f"get_pending_round(session_id={session_id}, round_index={round_index})"
        )
        await self._clear_expired()

        for pending in self._store.values():
            if (
                pending.metadata.session_id == session_id
                and pending.metadata.round_index == round_index
            ):
                return pending
        return None

    async def _clear_expired(self) -> None:
        now = self._now()
        expired_ids = [gid for gid, exp in self._expires_at.items() if now >= exp]
        for gid in expired_ids:
            self._store.pop(gid, None)
            self._expires_at.pop(gid, None)
            self._ready.pop(gid, None)

    def clear_all(self):
        """Clear all pending data - for testing purposes."""
        self._store.clear()
        self._expires_at.clear()
        self._ready.clear()


class RedisPendingStore(PendingBoardsStore):
    def __init__(self):
        self.redis: Redis = redis_client  # type: ignore
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


_pending_store: PendingBoardsStore = (
    RedisPendingStore() if REDIS_URL else InMemoryPendingStore()
)


def get_pending_boards_store() -> PendingBoardsStore:
    return _pending_store


def clear_pending_boards_store():
    """Clear the pending store - for testing purposes."""
    if hasattr(_pending_store, "clear_all"):
        _pending_store.clear_all()  # type: ignore
