import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class GameplaySettings:
    mode: Literal["normal", "hardcore"] = "normal"


@dataclass
class PendingGameplay:
    gameplay_id: uuid.UUID
    settings: GameplaySettings
    board_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None


class PendingStore(ABC):
    @abstractmethod
    async def create_pending(
        self,
        gameplay_id: uuid.UUID,
        settings: GameplaySettings,
        user_id: Optional[uuid.UUID],
        ttl_seconds: int,
    ) -> PendingGameplay: ...

    @abstractmethod
    async def mark_ready(self, gameplay_id: uuid.UUID, board_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def wait_for_ready(
        self, gameplay_id: uuid.UUID, timeout: float | None = None
    ) -> Optional[PendingGameplay]: ...

    @abstractmethod
    async def is_pending(self, gameplay_id: uuid.UUID) -> bool: ...


class InMemoryPendingStore(PendingStore):
    """In-memory implementation with lazy TTL expiry."""

    def __init__(self) -> None:
        self._store: dict[uuid.UUID, PendingGameplay] = {}
        self._expires_at: dict[uuid.UUID, float] = {}
        self._ready: dict[uuid.UUID, bool] = {}

    def _now(self) -> float:
        return time.time()

    def _is_expired(self, gameplay_id: uuid.UUID) -> bool:
        exp = self._expires_at.get(gameplay_id)
        return exp is None or self._now() >= exp

    async def create_pending(
        self,
        gameplay_id: uuid.UUID,
        settings: GameplaySettings,
        user_id: Optional[uuid.UUID],
        ttl_seconds: int,
    ) -> PendingGameplay:
        await self._clear_expired()
        now = self._now()
        pending = PendingGameplay(
            gameplay_id=gameplay_id, user_id=user_id, board_id=None, settings=settings
        )

        self._store[gameplay_id] = pending
        self._expires_at[gameplay_id] = now + ttl_seconds
        self._ready[gameplay_id] = False

        return pending

    async def mark_ready(self, gameplay_id: uuid.UUID, board_id: uuid.UUID) -> None:
        await self._clear_expired()
        self._store[gameplay_id].board_id = board_id
        self._ready[gameplay_id] = True

    async def wait_for_ready(
        self, gameplay_id: uuid.UUID, timeout: float | None = None
    ) -> Optional[PendingGameplay]:
        if gameplay_id not in self._store or self._is_expired(gameplay_id):
            self._store.pop(gameplay_id, None)
            self._expires_at.pop(gameplay_id, None)
            self._ready.pop(gameplay_id, None)
            return None

        if self._ready.get(gameplay_id, False):
            return self._store[gameplay_id]

        start_time = self._now()
        while True:
            await asyncio.sleep(0.1)
            if self._ready.get(gameplay_id, False):
                return self._store[gameplay_id]

            if timeout is not None and (self._now() - start_time) >= timeout:
                return None

    async def is_pending(self, gameplay_id: uuid.UUID) -> bool:
        await self._clear_expired()
        return gameplay_id in self._store

    async def _clear_expired(self) -> None:
        now = self._now()
        expired_ids = [gid for gid, exp in self._expires_at.items() if now >= exp]
        for gid in expired_ids:
            self._store.pop(gid, None)
            self._expires_at.pop(gid, None)
            self._ready.pop(gid, None)


pending_store: PendingStore = InMemoryPendingStore()
