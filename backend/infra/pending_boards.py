import asyncio
import time
import uuid
from typing import Optional

from backend.services.protocols.pending_boards_store_protocol import (
    GameplayOrSessionID,
    PendingBoardsStore,
)
from backend.services.single.pending_boards import PendingBoard, PendingBoardMetadata


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
        await self._clear_expired()
        now = self._now()
        pending = PendingBoard(
            generation_id=generation_id,
            metadata=metadata,
        )

        self._store[generation_id] = pending
        self._expires_at[generation_id] = now + ttl_seconds
        self._ready[generation_id] = False

        return pending

    async def mark_ready(self, generation_id: uuid.UUID) -> None:
        await self._clear_expired()
        self._ready[generation_id] = True

    async def wait_for_ready(
        self, generation_id: uuid.UUID, timeout: float | None = None
    ) -> Optional[PendingBoard]:
        if generation_id not in self._store or self._is_expired(generation_id):
            self._store.pop(generation_id, None)
            self._expires_at.pop(generation_id, None)
            self._ready.pop(generation_id, None)
            return None

        if self._ready.get(generation_id, False):
            return self._store[generation_id]

        start_time = self._now()
        while True:
            await asyncio.sleep(0.1)
            if self._ready.get(generation_id, False):
                return self._store[generation_id]

            if timeout is not None and (self._now() - start_time) >= timeout:
                return None

    async def is_pending(self, id: GameplayOrSessionID) -> bool:
        await self._clear_expired()

        for pending in self._store.values():
            if pending.metadata.gameplay_id == id:
                return True
        return False

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


_pending_store: PendingBoardsStore = InMemoryPendingStore()


def get_pending_boards_store() -> PendingBoardsStore:
    return _pending_store


def clear_pending_boards_store():
    """Clear the pending store - for testing purposes."""
    if hasattr(_pending_store, "clear_all"):
        _pending_store.clear_all()
