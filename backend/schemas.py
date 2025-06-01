from fastapi_users.schemas import BaseUser, BaseUserCreate

from .db import *
from .models import *
from uuid import UUID


class UserCreate(BaseUserCreate):
    nickname: str
    generator_settings: str


class UserRead(BaseUser[UUID]):
    nickname: str

    class Config:
        from_attributes = True


class UserUpdate(BaseUserCreate):
    nickname: str
