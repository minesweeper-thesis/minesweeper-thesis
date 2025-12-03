import uuid
from typing import Optional, Protocol

from backend.protocols.pending_boards import PendingBoard, PendingBoardMetadata


class PendingBoardsStore(Protocol):
    async def get_pending_gameplay(
        self, gameplay_id: uuid.UUID
    ) -> Optional[PendingBoard]: ...

    async def get_pending_round(
        self, session_id: uuid.UUID, round_index: int
    ) -> Optional[PendingBoard]: ...

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


__all__ = ["PendingBoardsStore"]
