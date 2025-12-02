import uuid
from typing import Optional, Protocol

from backend.services.single.pending_boards import PendingBoard, PendingBoardMetadata

type GameplayOrSessionID = uuid.UUID


class PendingBoardsStore(Protocol):
    async def is_pending(self, id: GameplayOrSessionID) -> bool: ...

    async def mark_ready(self, generation_id: uuid.UUID) -> None: ...

    async def wait_for_ready(
        self, generation_id: uuid.UUID, timeout: float
    ) -> Optional["PendingBoard"]: ...

    async def create_pending(
        self,
        generation_id: uuid.UUID,
        metadata: PendingBoardMetadata,
        ttl_seconds: int,
    ) -> PendingBoard: ...


__all__ = ["PendingBoardsStore", "GameplayOrSessionID"]
