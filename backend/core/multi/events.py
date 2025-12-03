import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserReady:
    session_id: uuid.UUID
    round_index: int
    user_id: uuid.UUID


@dataclass
class RoundCountdown:
    session_id: uuid.UUID
    round_index: int
    start_at: datetime


__all__ = ["UserReady", "RoundCountdown"]
