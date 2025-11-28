import uuid
from typing import Literal, Self

from backend.core.game import *
from backend.core.multiplayer.session import NotReadyMessage, ReadyMessage
from backend.routers.schemas import Request, Response
from backend.services.lobby_service import (
    GameReadyMessage,
    RoundEndMessage,
    RoundStartMessage,
    SessionOverMessage,
)


class ReadyRequest(Request):
    ws_type: Literal["ready"] = "ready"

    def to_core(self) -> "ReadyMessage":
        return ReadyMessage()


class CancelReadyRequest(Request):
    ws_type: Literal["not_ready"] = "not_ready"

    def to_core(self) -> "NotReadyMessage":
        return NotReadyMessage()


class RoundStartResponse(Response):
    ws_type: Literal["round_start"] = "round_start"
    session_id: uuid.UUID
    round: int
    start_at: int
    end_at: int
    start_field: Cell

    @classmethod
    def from_core(cls, message: "RoundStartMessage") -> Self:
        return cls(
            start_at=message.start_at,
            end_at=message.end_at,
            session_id=message.session_id,
            round=message.round,
            start_field=message.start_field,
        )


class RoundEndResponse(Response):
    ws_type: Literal["round_end"] = "round_end"
    session_id: uuid.UUID
    round: int

    @classmethod
    def from_core(cls, message: "RoundEndMessage") -> Self:
        return cls(
            session_id=message.session_id,
            round=message.round,
        )


class SessionOverResponse(Response):
    ws_type: Literal["session_over"] = "session_over"
    session_id: uuid.UUID

    @classmethod
    def from_core(cls, message: "SessionOverMessage") -> Self:
        return cls(
            session_id=message.session_id,
        )


class FirstRoundStartResponse(RoundStartResponse):
    gameplay_id: uuid.UUID


class GameReadyResponse(Response):
    ws_type: Literal["ready"] = "ready"
    session_id: uuid.UUID
    round: int
    start_at: int

    @classmethod
    def from_core(cls, message: "GameReadyMessage") -> Self:
        return cls(
            session_id=message.session_id,
            round=message.round,
            start_at=message.start_at,
        )


__all__ = [
    "RoundStartResponse",
    "RoundEndResponse",
    "SessionOverResponse",
    "FirstRoundStartResponse",
    "GameReadyResponse",
]
