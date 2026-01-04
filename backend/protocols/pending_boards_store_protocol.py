import uuid
from dataclasses import dataclass
from typing import Optional, Protocol

from backend.core.board import DifficultyLevel, GenerationSettings
from backend.core.game.types import GameMode


@dataclass
class PendingBoardMetadata:
    generation_settings: GenerationSettings
    difficulty_level: DifficultyLevel
    mode: GameMode
    gameplay_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None


@dataclass
class PendingBoard:
    generation_id: uuid.UUID
    metadata: PendingBoardMetadata
    board_id: Optional[uuid.UUID] = None


class PendingBoardsStore(Protocol):
    async def get_pending_gameplay(
        self, gameplay_id: uuid.UUID
    ) -> Optional[PendingBoard]: ...

    async def create_pending(
        self, generation_id: uuid.UUID, metadata: PendingBoardMetadata
    ) -> PendingBoard: ...

    async def delete_pending(self, generation_id: uuid.UUID) -> None: ...

    async def mark_ready(
        self, generation_id: uuid.UUID, board_id: uuid.UUID
    ) -> None: ...

    async def wait_for_ready(
        self, generation_id: uuid.UUID
    ) -> Optional["PendingBoard"]: ...


__all__ = ["PendingBoardsStore"]
