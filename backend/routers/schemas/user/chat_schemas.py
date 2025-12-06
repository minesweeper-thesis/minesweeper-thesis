import uuid
from typing import Literal, Self

from pydantic import BaseModel

from backend.core.user.chat import UserChatMessage
from backend.routers.schemas import Response
from backend.routers.schemas.user.user_schemas import UserResponse


class UserChatMessageRequest(BaseModel):
    user_id: uuid.UUID
    content: str


class UserChatMessageResponse(Response):
    ws_type: Literal["user_chat_message"] = "user_chat_message"
    user: UserResponse
    content: str
    timestamp: int

    @classmethod
    def build(cls, message: UserChatMessage) -> Self:
        return cls(
            user=UserResponse.build(message.from_user),
            content=message.content,
            timestamp=int(message.timestamp.timestamp()),
        )


__all__ = ["UserChatMessageRequest", "UserChatMessageResponse"]
