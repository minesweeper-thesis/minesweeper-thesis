import uuid
from dataclasses import dataclass
from datetime import datetime

from backend.core.board import DifficultyLevel
from backend.core.game import Cell


@dataclass
class UserReady:
    user_id: uuid.UUID
    round_index: int
    ready: bool


@dataclass
class RoundReady:
    session_id: uuid.UUID
    round_index: int
    difficulty_level: DifficultyLevel


@dataclass
class RoundCountdown:
    session_id: uuid.UUID
    round_index: int
    countdown_to: datetime
    start_at: datetime
    start_field: Cell


__all__ = ["UserReady", "RoundReady", "RoundCountdown"]
