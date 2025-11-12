import uuid
from typing import TYPE_CHECKING, Optional

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import JSON, CheckConstraint, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.user import (
    Avatar,
    FriendRequest,
    FriendRequestStatus,
    Friendship,
    User,
)
from backend.repositories.orm import Base

if TYPE_CHECKING:
    from .game_orm import SingleplayerGameplayORM


class UserORM(SQLAlchemyBaseUserTable[uuid.UUID], Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    nickname: Mapped[str] = mapped_column()
    settings: Mapped[dict] = mapped_column(JSON, default={})
    avatar_url: Mapped[Optional[str]] = mapped_column()

    singleplayer_gameplays: Mapped[list["SingleplayerGameplayORM"]] = relationship(
        back_populates="user", cascade="all, delete"
    )
    friends: Mapped[list["FriendshipORM"]] = relationship(
        foreign_keys=lambda: FriendshipORM.user_id,
        back_populates="user",
    )
    friend_of: Mapped[list["FriendshipORM"]] = relationship(
        foreign_keys=lambda: FriendshipORM.friend_id,
        back_populates="friend",
    )
    sent_friend_requests: Mapped[list["FriendRequestORM"]] = relationship(
        foreign_keys=lambda: FriendRequestORM.user_id,
        back_populates="user",
    )
    received_friend_requests: Mapped[list["FriendRequestORM"]] = relationship(
        foreign_keys=lambda: FriendRequestORM.friend_id,
        back_populates="friend",
    )

    def to_user(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            nickname=self.nickname,
            settings=self.settings,
            avatar=Avatar(url=self.avatar_url) if self.avatar_url else None,
        )


class FriendshipORM(Base):
    __tablename__ = "friendships"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(UserORM.id), primary_key=True)
    friend_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(UserORM.id), primary_key=True
    )

    user: Mapped[UserORM] = relationship(foreign_keys=user_id, back_populates="friends")
    friend: Mapped[UserORM] = relationship(
        foreign_keys=friend_id, back_populates="friend_of"
    )

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_friend"),
    )

    def to_friendship(self) -> "Friendship":
        return Friendship(user=self.user, friend=self.friend)

    @staticmethod
    def from_friendship(friendship: "Friendship") -> "FriendshipORM":
        return FriendshipORM(
            user_id=friendship.user.id,
            friend_id=friendship.friend.id,
        )


class FriendRequestORM(Base):
    __tablename__ = "friend_requests"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(UserORM.id), primary_key=True)
    friend_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(UserORM.id), primary_key=True
    )
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus),
        default="pending",
    )

    user: Mapped[UserORM] = relationship(
        foreign_keys=user_id, back_populates="sent_friend_requests"
    )
    friend: Mapped[UserORM] = relationship(
        foreign_keys=friend_id, back_populates="received_friend_requests"
    )

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_request"),
    )

    def to_friend_request(self) -> "FriendRequest":
        return FriendRequest(
            id=self.id,
            user=self.user.to_user(),
            friend=self.friend.to_user(),
            status=self.status,
        )

    @staticmethod
    def from_friend_request(friend_request: "FriendRequest") -> "FriendRequestORM":
        return FriendRequestORM(
            id=friend_request.id,
            user_id=friend_request.user.id,
            friend_id=friend_request.friend.id,
            status=friend_request.status,
        )


__all__ = ["UserORM", "FriendshipORM", "FriendRequestORM"]
