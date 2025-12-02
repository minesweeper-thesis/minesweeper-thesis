import uuid
from typing import Literal, Self

from pydantic import BaseModel

from backend.core.lobby import *
from backend.routers.schemas import Response

from ..user import UserResponse


class ChatMessageRequest(BaseModel):
    content: str


class ChatMessageResponse(Response):
    ws_type: Literal["chat_message"] = "chat_message"
    sender: UserResponse
    lobby_id: uuid.UUID
    content: str
    timestamp: int

    @classmethod
    def build(cls, message: ChatMessage) -> Self:
        return cls(
            sender=UserResponse.build(message.sender),
            lobby_id=message.lobby_id,
            content=message.content,
            timestamp=message.timestamp,
        )


__all__ = ["ChatMessageRequest", "ChatMessageResponse"]
