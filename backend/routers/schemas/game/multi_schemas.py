import uuid
from typing import Literal, Self

from backend.core.game import *
from backend.core.multi.events import RoundCountdown, UserReady
from backend.core.multi.round import RoundEnd, RoundStart
from backend.core.multi.session import SessionOver
from backend.routers.schemas import Response


class RoundStartResponse(Response):
    ws_type: Literal["round_start"] = "round_start"
    session_id: uuid.UUID
    round: int
    start_at: int
    end_at: int
    start_field: Cell

    @classmethod
    def build(cls, message: "RoundStart") -> Self:
        return cls(
            start_at=int(message.start_at.timestamp()),
            end_at=int(message.end_at.timestamp()),
            session_id=message.session_id,
            round=message.round,
            start_field=message.start_field,
        )


class RoundEndResponse(Response):
    ws_type: Literal["round_end"] = "round_end"
    session_id: uuid.UUID
    round: int

    @classmethod
    def build(cls, message: "RoundEnd") -> Self:
        return cls(
            session_id=message.session_id,
            round=message.round,
        )


class SessionOverResponse(Response):
    ws_type: Literal["session_over"] = "session_over"
    session_id: uuid.UUID

    @classmethod
    def build(cls, message: "SessionOver") -> Self:
        return cls(
            session_id=message.session_id,
        )


class RoundReadyResponse(Response):
    ws_type: Literal["ready"] = "ready"
    session_id: uuid.UUID
    round_index: int
    start_at: int

    @classmethod
    def build(cls, message: RoundCountdown) -> Self:
        return cls(
            session_id=message.session_id,
            round_index=message.round_index,
            start_at=int(message.start_at.timestamp()),
        )


class UserReadyResponse(Response):
    ws_type: Literal["user_ready"] = "user_ready"
    session_id: uuid.UUID
    round_index: int
    user_id: uuid.UUID

    @classmethod
    def build(cls, message: "UserReady") -> Self:
        return cls(
            session_id=message.session_id,
            round_index=message.round_index,
            user_id=message.user_id,
        )


__all__ = [
    "RoundStartResponse",
    "RoundEndResponse",
    "SessionOverResponse",
    "RoundReadyResponse",
    "UserReadyResponse",
]
