import uuid
from typing import Awaitable, Callable, Literal, Protocol

from backend.core.board import GenerationSettings

type GenerationID = uuid.UUID
type GenerationStatus = Literal["pending", "in_progress", "completed", "failed"]

type OnBoardGeneratedCallback = Callable[[GenerationID, uuid.UUID], Awaitable[None]]


class GenerationNotFound(Exception):
    pass


class BoardGenerator(Protocol):
    async def generate_board(
        self,
        settings: GenerationSettings,
        on_completed: OnBoardGeneratedCallback,
    ) -> GenerationID: ...

    async def get_generation_status(
        self, generation_id: GenerationID
    ) -> GenerationStatus: ...


__all__ = [
    "GenerationID",
    "BoardGenerator",
    "GenerationNotFound",
    "GenerationStatus",
    "OnBoardGeneratedCallback",
]
