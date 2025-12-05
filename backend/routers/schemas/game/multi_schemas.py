import uuid
from dataclasses import asdict
from typing import Literal, Optional, Self

from backend.core.game import *
from backend.core.multi import (
    RoundEnd,
    RoundScoreItem,
    RoundStart,
    ScoreUpdate,
    SessionOver,
    SessionScoreItem,
)
from backend.routers.schemas import Response
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
    value: bool = True

    @classmethod
    def build(cls, message: "UserReady") -> Self:
        return cls(
            round=message.round_index + 1,
            user_id=message.user_id,
        )


class UserNotReadyResponse(Response):
    ws_type: Literal["user_ready"] = "user_ready"
    round: int
    user_id: uuid.UUID
    value: bool = False

    @classmethod
    def build(cls, message: "UserNotReady") -> Self:
        return cls(
            round=message.round_index + 1,
            user_id=message.user_id,
        )


class RoundReadyResponse(Response):
    ws_type: Literal["round_ready"] = "round_ready"
    session_id: uuid.UUID
    round: int

    @classmethod
    def build(cls, message: RoundReady) -> Self:
        return cls(
            session_id=message.session_id,
            round=message.round_index + 1,
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


__all__ = [
    "RoundStartResponse",
    "RoundEndResponse",
    "SessionOverResponse",
    "RoundCountdownResponse",
    "RoundReadyResponse",
    "UserReadyResponse",
    "UserNotReadyResponse",
    "ScoreUpdateResponse",
]
