import uuid
from typing import Literal, Self

from pydantic import BaseModel

from backend.core.lobby import *
from backend.schemas import Response
from backend.schemas.user import UserResponse


class LobbyChatMessageRequest(BaseModel):
    content: str


class LobbyChatMessageResponse(Response):
    ws_type: Literal["lobby_chat_message"] = "lobby_chat_message"
    sender: UserResponse
    lobby_id: uuid.UUID
    content: str
    timestamp: int

    @classmethod
    def build(cls, message: LobbyChatMessage) -> Self:
        return cls(
            sender=UserResponse.build(message.sender),
            lobby_id=message.lobby_id,
            content=message.content,
            timestamp=int(message.timestamp.timestamp()),
        )


__all__ = ["LobbyChatMessageRequest", "LobbyChatMessageResponse"]
