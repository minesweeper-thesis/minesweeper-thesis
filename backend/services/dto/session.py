import uuid
from dataclasses import dataclass
from typing import Literal, Optional

from backend.core.multi import SessionScoreboard
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


__all__ = [
    "RoundSchedule",
    "SessionState",
    "SessionStateRoundData",
]
