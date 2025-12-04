import uuid
from typing import Literal

from pydantic import BaseModel

from backend.core.user import FriendRequest, FriendRequestStatus
from backend.routers.schemas import Response

from .user_schemas import UserResponse


class MakeFriendRequest(BaseModel):
    friend_id: uuid.UUID


class FriendRequestResponse(Response):
    ws_type: Literal["friend_request"] = "friend_request"
    id: uuid.UUID
    user: UserResponse
    friend: UserResponse
    status: FriendRequestStatus

    @classmethod
    def build(cls, friend_request: FriendRequest) -> "FriendRequestResponse":
        return cls(
            id=friend_request.id,
            user=UserResponse.build(friend_request.user),
            friend=UserResponse.build(friend_request.friend),
            status=friend_request.status,
        )


__all__ = [
    "MakeFriendRequest",
    "FriendRequestResponse",
]
