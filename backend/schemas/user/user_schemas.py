import uuid
from typing import Optional

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import BaseModel

from backend.core.single.gameplay import SingleplayerGameplay
from backend.core.user import User
from backend.schemas import Response


class UserCreateRequest(BaseUserCreate):
    nickname: str
    settings: dict = {}


class UserResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    email: str
    is_online: bool = False
    avatar_url: Optional[str] = None

    @classmethod
    def build(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            is_online=user.is_online,
            avatar_url=user.avatar.url if user.avatar else None,
        )


class CurrentUserResponse(BaseUser[uuid.UUID], UserResponse):
    settings: dict


class UserUpdateRequest(BaseUserUpdate):
    nickname: str
    settings: dict


class UserGameplayResponse(Response):
    id: uuid.UUID
    board_id: uuid.UUID
    status: str
    result: Optional[str]
    used_hints: int
    elapsed_time: float
    game_mode: str

    @classmethod
    def build(cls, gameplay: "SingleplayerGameplay") -> "UserGameplayResponse":
        return cls(
            id=gameplay.id,
            board_id=gameplay.board.id,
            status=gameplay.status,
            result=gameplay.result,
            used_hints=gameplay.used_hints,
            elapsed_time=gameplay.elapsed_time,
            game_mode=gameplay.game_mode,
        )


__all__ = [
    "UserCreateRequest",
    "UserResponse",
    "CurrentUserResponse",
    "UserUpdateRequest",
    "UserGameplayResponse",
]
