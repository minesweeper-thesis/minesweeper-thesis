import uuid
from typing import Optional, Protocol

from backend.core.board import *
from backend.core.board import Minefields
from backend.core.user import User


class BoardRepository(Protocol):
    async def add_board(self, board: Board) -> None: ...

    async def get_board_by_id(self, board_id: uuid.UUID) -> Board: ...

    async def get_board(
        self,
        difficulty_level: Optional[DifficultyLevel] = None,
        minefields: Optional[Minefields] = None,
        generation_settings: Optional[GenerationSettings] = None,
    ) -> Board: ...

    async def get_unsolved_board(
        self,
        difficulty_level: DifficultyLevel,
        *,
        generation_settings: Optional[GenerationSettings] = None,
        user: Optional[User] = None,
    ) -> Board: ...


__all__ = ["BoardRepository"]
