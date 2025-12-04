import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserReady:
    user_id: uuid.UUID
    round_index: int


@dataclass
class RoundReady:
    session_id: uuid.UUID
    round_index: int


@dataclass
class RoundCountdown:
    session_id: uuid.UUID
    round_index: int
    start_at: datetime


__all__ = ["UserReady", "RoundReady", "RoundCountdown"]
