import uuid

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import BaseModel, ConfigDict

from backend.models import FriendRequestStatus


class UserCreate(BaseUserCreate):
    nickname: str
    generator_settings: str


class UserRead(BaseUser[uuid.UUID]):
    nickname: str


class UserUpdate(BaseUserUpdate):
    nickname: str


class FriendRequest(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    friend_id: uuid.UUID
    status: FriendRequestStatus

    model_config = ConfigDict(from_attributes=True)


class Friend(BaseModel):
    id: uuid.UUID
    nickname: str

    model_config = ConfigDict(from_attributes=True)
