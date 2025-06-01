import uuid

from fastapi_users.schemas import BaseUser, BaseUserCreate

from ..db import *
from ..models import *


class UserCreate(BaseUserCreate):
    nickname: str
    generator_settings: str


class UserRead(BaseUser[uuid.UUID]):
    nickname: str

    class Config:
        from_attributes = True


class UserUpdate(BaseUserCreate):
    nickname: str
