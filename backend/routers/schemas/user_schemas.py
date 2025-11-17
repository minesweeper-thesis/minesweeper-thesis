import uuid
from typing import Optional

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import BaseModel

from backend.core.singleplayer import SingleplayerGameplay
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

    @classmethod
    def from_friend_request(
        cls, friend_request: FriendRequest
    ) -> "FriendRequestResponse":
        return cls(
            id=friend_request.id,
            user=UserResponse.from_user(friend_request.user),
            friend=UserResponse.from_user(friend_request.friend),
            status=friend_request.status,
        )


class FriendRequestNotificationResponse(FriendRequestResponse):
    type: str = "friend_request"


class FriendResponse(UserResponse):
    @staticmethod
    def from_user(user: User) -> "FriendResponse":
        return FriendResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatar_url=user.avatar.url if user.avatar else None,
        )


class UserGameplayResponse(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    status: str
    result: Optional[str]
    used_hints: int
    elapsed_time: float
    game_mode: str

    @staticmethod
    def from_gameplay(gameplay: "SingleplayerGameplay") -> "UserGameplayResponse":
        return UserGameplayResponse(
            id=gameplay.id,
            board_id=gameplay.board.id,
            status=gameplay.status,
            result=gameplay.result,
            used_hints=gameplay.used_hints,
            elapsed_time=gameplay.elapsed_time,
            game_mode=gameplay.game_mode,
        )
