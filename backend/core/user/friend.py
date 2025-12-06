import enum
import uuid

from backend.core.user.user import User


class FriendRequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


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


__all__ = ["FriendRequest", "FriendRequestStatus", "Friendship"]
