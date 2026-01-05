import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.board import DifficultyLevel
from backend.core.game.types import *
from backend.core.multi import Generator


@dataclass
class NewGameSettings:
    board_id: Optional[uuid.UUID]
    generator: Optional[Generator]
    difficulty_level: Optional[DifficultyLevel]
    mode: GameMode


__all__ = ["NewGameSettings"]
