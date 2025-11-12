import enum
import uuid
from dataclasses import dataclass
from typing import Optional


class FriendRequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


@dataclass
class Avatar:
    url: str


class User:
    def __init__(
        self,
        id: uuid.UUID,
        nickname: str,
        email: str,
        settings: dict,
        avatar: Optional[Avatar] = None,
    ):
        self.id = id
        self.nickname = nickname
        self.email = email
        self.settings = settings
        self.avatar = avatar

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, User):
            return False
        return self.id == value.id


class FriendRequest:
    def __init__(
        self,
        id: uuid.UUID,
        user: User,
        friend: User,
        status: FriendRequestStatus,
    ):
        self.id = id
        self.user = user
        self.friend = friend
        self.status = status

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, FriendRequest):
            return False
        return self.id == value.id


class Friendship:
    def __init__(self, user: User, friend: User):
        self.user = user
        self.friend = friend

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Friendship):
            return False
        return self.user == value.user and self.friend == value.friend
