import enum
import uuid
from typing import TYPE_CHECKING

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import CheckConstraint, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .game import Gameplay


class Friendship(Base):
    __tablename__ = "friendship"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    friend_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id"), primary_key=True
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="friends"
    )
    friend: Mapped["User"] = relationship(
        "User", foreign_keys=[friend_id], back_populates="friend_of"
    )

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_friend"),
    )


class FriendRequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class FriendRequest(Base):
    __tablename__ = "friend_request"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    friend_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id"), primary_key=True
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="sent_friend_requests"
    )
    friend: Mapped["User"] = relationship(
        "User", foreign_keys=[friend_id], back_populates="received_friend_requests"
    )

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_request"),
    )
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friend_request_status"),
        nullable=False,
        default=FriendRequestStatus.pending,
    )


class User(Base, SQLAlchemyBaseUserTableUUID):
    __tablename__ = "user"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    nickname: Mapped[str] = mapped_column(nullable=False, index=True)
    generator_settings: Mapped[str] = mapped_column(nullable=False)

    boards: Mapped[list["Gameplay"]] = relationship(
        "Gameplay", back_populates="user", cascade="all, delete"
    )
    friends: Mapped[list[Friendship]] = relationship(
        "Friendship", foreign_keys=[Friendship.user_id], back_populates="user"
    )
    friend_of: Mapped[list[Friendship]] = relationship(
        "Friendship", foreign_keys=[Friendship.friend_id], back_populates="friend"
    )
    sent_friend_requests: Mapped[list[FriendRequest]] = relationship(
        "FriendRequest",
        foreign_keys=[FriendRequest.user_id],
        back_populates="user",
    )
    received_friend_requests: Mapped[list[FriendRequest]] = relationship(
        "FriendRequest",
        foreign_keys=[FriendRequest.friend_id],
        back_populates="friend",
    )
