import uuid
from typing import Literal, Optional

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import BaseModel

from backend.core.singleplayer import SingleplayerGameplay
from backend.core.user import FriendRequest, FriendRequestStatus, User
from backend.routers.schemas import Response


class UserCreateRequest(BaseUserCreate):
    nickname: str
    settings: dict = {}


class UserResponse(Response):
    id: uuid.UUID
    nickname: str
    email: str
    avatar_url: Optional[str] = None

    @classmethod
    def from_core(cls, user: User) -> "UserResponse":
        return cls(
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


class FriendRequestResponse(Response):
    id: uuid.UUID
    user: UserResponse
    friend: UserResponse
    status: FriendRequestStatus

    @classmethod
    def from_core(cls, friend_request: FriendRequest) -> "FriendRequestResponse":
        return cls(
            id=friend_request.id,
            user=UserResponse.from_core(friend_request.user),
            friend=UserResponse.from_core(friend_request.friend),
            status=friend_request.status,
        )


class FriendRequestNotificationResponse(FriendRequestResponse):
    ws_type: Literal["friend_request"] = "friend_request"


class UserGameplayResponse(Response):
    id: uuid.UUID
    board_id: uuid.UUID
    status: str
    result: Optional[str]
    used_hints: int
    elapsed_time: float
    game_mode: str

    @classmethod
    def from_core(cls, gameplay: "SingleplayerGameplay") -> "UserGameplayResponse":
        return cls(
            id=gameplay.id,
            board_id=gameplay.board.id,
            status=gameplay.status,
            result=gameplay.result,
            used_hints=gameplay.used_hints,
            elapsed_time=gameplay.elapsed_time,
            game_mode=gameplay.game_mode,
        )
