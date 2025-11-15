import uuid
from typing import ClassVar, Optional

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import BaseModel

from backend.core.user import FriendRequest, FriendRequestStatus, User


class UserCreateRequest(BaseUserCreate):
    nickname: str
    settings: dict = {}


class UserResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    email: str
    avatar_url: Optional[str] = None

    @staticmethod
    def from_user(user: User) -> "UserResponse":
        return UserResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar.url if user.avatar else None,
        )


class CurrentUserResponse(BaseUser[uuid.UUID], UserResponse):
    settings: dict


class UserUpdateRequest(BaseUserUpdate):
    nickname: str
    settings: dict


class MakeFriendRequest(BaseModel):
    friend_id: uuid.UUID


class FriendRequestResponse(BaseModel):
    id: uuid.UUID
    user: UserResponse
    friend: UserResponse
    status: FriendRequestStatus

    @staticmethod
    def from_friend_request(friend_request: FriendRequest) -> "FriendRequestResponse":
        return FriendRequestResponse(
            id=friend_request.id,
            user=UserResponse.from_user(friend_request.user),
            friend=UserResponse.from_user(friend_request.friend),
            status=friend_request.status,
        )


class FriendRequestNotificationResponse(FriendRequestResponse):
    type: ClassVar[str] = "friend_request"


class FriendResponse(UserResponse):
    @staticmethod
    def from_user(user: User) -> "FriendResponse":
        return FriendResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar.url if user.avatar else None,
        )
