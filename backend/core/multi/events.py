import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AllReady:
    session_id: uuid.UUID
    round_index: int


@dataclass
class RoundStartAwaiting:
    session_id: uuid.UUID
    round_index: int
    start_at: datetime


__all__ = ["AllReady", "RoundStartAwaiting"]
