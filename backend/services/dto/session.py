import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from backend.core.game.types import Cell
from backend.core.multi import SessionScoreboard
from backend.core.multi.score import RoundScoreboard
from backend.protocols.session_runtime_store_protocol import RoundSchedule


@dataclass
class SessionStateRoundData:
    round_number: int
    schedule: Optional[RoundSchedule]
    state: Literal["not_ready", "generating", "countdown", "ready_lock", "playing"]


@dataclass
class SessionState:
    session_id: uuid.UUID
    round: SessionStateRoundData
    scoreboard: SessionScoreboard


@dataclass
class RoundStart:
    session_id: uuid.UUID
    round_index: int
    start_at: datetime
    end_at: datetime
    start_field: Cell


@dataclass
class RoundEnd:
    session_id: uuid.UUID
    round_index: int
    scoreboard: RoundScoreboard


@dataclass
class SessionOver:
    session_id: uuid.UUID
    scoreboard: SessionScoreboard


__all__ = [
    "RoundSchedule",
    "SessionState",
    "SessionStateRoundData",
    "RoundStart",
    "RoundEnd",
    "SessionOver",
]
