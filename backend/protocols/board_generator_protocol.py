import uuid
from typing import Any, Callable, Coroutine, Protocol

from backend.core.board import Board, GenerationSettings

type GenerationID = uuid.UUID

type OnBoardGeneratedCallback = Callable[
    [GenerationID, Board], Coroutine[Any, Any, None]
]


class GenerationNotFound(Exception):
    pass


class BoardGenerator(Protocol):
    async def generate_board(
        self,
        settings: GenerationSettings,
        on_completed: OnBoardGeneratedCallback,
    ) -> GenerationID: ...


class SingleBoardGenerator(BoardGenerator, Protocol):
    pass


class MultiBoardGenerator(BoardGenerator, Protocol):
    pass


__all__ = [
    "GenerationID",
    "GenerationNotFound",
    "OnBoardGeneratedCallback",
    "BoardGenerator",
    "SingleBoardGenerator",
    "MultiBoardGenerator",
]
