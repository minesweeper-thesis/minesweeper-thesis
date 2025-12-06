import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.board import DifficultyLevel, GenerationSettings
from backend.core.game.types import GameMode


@dataclass
class PendingBoardMetadata:
    generation_settings: GenerationSettings
    difficulty_level: DifficultyLevel
    mode: GameMode
    gameplay_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    round_index: Optional[int] = None


@dataclass
class PendingBoard:
    generation_id: uuid.UUID
    metadata: PendingBoardMetadata
    board_id: Optional[uuid.UUID] = None


__all__ = ["PendingBoard", "PendingBoardMetadata"]
