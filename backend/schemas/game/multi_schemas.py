import uuid
from dataclasses import asdict
from typing import Literal, Optional, Self

from pydantic import BaseModel

from backend.core.board import DifficultyLevel
from backend.core.game import *
from backend.core.multi import RoundScoreItem, ScoreUpdate, SessionScoreItem
from backend.schemas import Response
from backend.services.dto import *


class RoundStartResponse(Response):
    ws_type: Literal["round_start"] = "round_start"
    round: int
    start_at: int
    end_at: int
    start_field: Cell

    @classmethod
    def build(cls, message: "RoundStart") -> Self:
        return cls(
            start_at=int(message.start_at.timestamp() * 1000),
            end_at=int(message.end_at.timestamp() * 1000),
            round=message.round_index + 1,
            start_field=message.start_field,
        )


class RoundEndResponse(Response):
    ws_type: Literal["round_end"] = "round_end"
    round: int
    scoreboard: list[RoundScoreItem]

    @classmethod
    def build(cls, message: "RoundEnd") -> Self:
        return cls(
            round=message.round_index + 1,
            scoreboard=message.scoreboard.items,
        )


class SessionOverResponse(Response):
    ws_type: Literal["session_over"] = "session_over"
    scoreboard: list[SessionScoreItem]

    @classmethod
    def build(cls, message: "SessionOver") -> Self:
        return cls(scoreboard=message.scoreboard.items)


class RoundCountdownResponse(Response):
    ws_type: Literal["round_countdown"] = "round_countdown"
    round: int
    countdown_to: int
    start_at: int
    start_field: Cell

    @classmethod
    def build(cls, message: RoundCountdown) -> Self:
        return cls(
            round=message.round_index + 1,
            countdown_to=int(message.countdown_to.timestamp() * 1000),
            start_at=int(message.start_at.timestamp() * 1000),
            start_field=message.start_field,
        )


class UserReadyResponse(Response):
    ws_type: Literal["user_ready"] = "user_ready"
    round: int
    user_id: uuid.UUID
    value: bool

    @classmethod
    def build(cls, message: "UserReady") -> Self:
        return cls(
            round=message.round_index + 1,
            user_id=message.user_id,
            value=message.ready,
        )


class RoundReadyResponse(Response):
    ws_type: Literal["round_ready"] = "round_ready"
    session_id: uuid.UUID
    round: int
    difficulty_level: DifficultyLevel

    @classmethod
    def build(cls, message: RoundReady) -> Self:
        return cls(
            session_id=message.session_id,
            round=message.round_index + 1,
            difficulty_level=message.difficulty_level,
        )


class ScoreUpdateResponse(Response):
    ws_type: Literal["score_update"] = "score_update"
    user_id: uuid.UUID
    score: float
    revealed_count: int
    status: GameStatus
    result: Optional[GameResult] = None
    loss_cause: Optional[LossCause] = None

    @classmethod
    def build(cls, message: ScoreUpdate) -> Self:
        return cls(**asdict(message.score))


class RoundData(BaseModel):
    number: int
    start_at: Optional[int]
    end_at: Optional[int]
    countdown_to: Optional[int]
    state: Literal["not_ready", "generating", "countdown", "ready_lock", "playing"]


class SessionStateResponse(Response):
    ws_type: Literal["session_state"] = "session_state"
    session_id: uuid.UUID
    round: RoundData
    scoreboard: list[SessionScoreItem]

    @classmethod
    def build(cls, message: SessionState) -> Self:
        start_at = (
            int(message.round.schedule.start_at.timestamp() * 1000)
            if message.round.schedule
            else None
        )
        end_at = (
            int(message.round.schedule.end_at.timestamp() * 1000)
            if message.round.schedule
            else None
        )
        countdown_to = (
            int(message.round.schedule.countdown_to.timestamp() * 1000)
            if message.round.schedule
            else None
        )

        return cls(
            session_id=message.session_id,
            round=RoundData(
                number=message.round.round_number,
                start_at=start_at,
                end_at=end_at,
                countdown_to=countdown_to,
                state=message.round.state,
            ),
            scoreboard=message.scoreboard.items,
        )


__all__ = [
    "RoundStartResponse",
    "RoundEndResponse",
    "SessionOverResponse",
    "RoundCountdownResponse",
    "RoundReadyResponse",
    "UserReadyResponse",
    "ScoreUpdateResponse",
    "SessionStateResponse",
]
