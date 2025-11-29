import uuid
from typing import Literal, Self

from backend.core.game import *
from backend.core.multi.round import RoundEnd, RoundStart
from backend.core.multi.session import (
    CancelReadyMessage,
    GameReady,
    ReadyMessage,
    SessionOver,
)
from backend.routers.schemas import Response, WSRequest


class ReadyRequest(WSRequest):
    ws_type: Literal["ready"] = "ready"

    def parse(self) -> "ReadyMessage":
        return ReadyMessage()


class CancelReadyRequest(WSRequest):
    ws_type: Literal["not_ready"] = "not_ready"

    def parse(self) -> "CancelReadyMessage":
        return CancelReadyMessage()


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


class FirstRoundStartResponse(RoundStartResponse):
    gameplay_id: uuid.UUID


class GameReadyResponse(Response):
    ws_type: Literal["ready"] = "ready"
    session_id: uuid.UUID
    round: int
    start_at: int

    @classmethod
    def build(cls, message: "GameReady") -> Self:
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
