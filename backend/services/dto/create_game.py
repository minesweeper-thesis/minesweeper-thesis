import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.board import DifficultyLevel, GenerationSettings
from backend.core.game.types import *


@dataclass
class NewGameSettings:
    board_id: Optional[uuid.UUID]
    generator: Optional[GenerationSettings]
    difficulty_level: Optional[DifficultyLevel]
    mode: GameMode


__all__ = ["NewGameSettings"]
