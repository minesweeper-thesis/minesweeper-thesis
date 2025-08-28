import enum
import uuid

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import CheckConstraint, Column, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Friendship(Base):
    __tablename__ = "friendship"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id = Column(Uuid, ForeignKey("user.id"), primary_key=True)
    friend_id = Column(Uuid, ForeignKey("user.id"), primary_key=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friend_of")

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_friend"),
    )


class FriendRequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class FriendRequest(Base):
    __tablename__ = "friend_request"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id = Column(Uuid, ForeignKey("user.id"), primary_key=True)
    friend_id = Column(Uuid, ForeignKey("user.id"), primary_key=True)

    user = relationship(
        "User", foreign_keys=[user_id], back_populates="sent_friend_requests"
    )
    friend = relationship(
        "User", foreign_keys=[friend_id], back_populates="received_friend_requests"
    )

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_request"),
    )
    status = Column(
        Enum(FriendRequestStatus, name="friend_request_status"),
        nullable=False,
        default="pending",
    )


class User(Base, SQLAlchemyBaseUserTableUUID):
    __tablename__ = "user"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    nickname = Column(String, nullable=False, index=True)
    generator_settings = Column(Text, nullable=False, index=True)

    boards = relationship("Gameplay", back_populates="user", cascade="all, delete")
    friends = relationship(
        "Friendship", foreign_keys=[Friendship.user_id], back_populates="user"
    )
    friend_of = relationship(
        "Friendship", foreign_keys=[Friendship.friend_id], back_populates="friend"
    )
    sent_friend_requests = relationship(
        "FriendRequest",
        foreign_keys=[FriendRequest.user_id],
        back_populates="user",
    )
    received_friend_requests = relationship(
        "FriendRequest",
        foreign_keys=[FriendRequest.friend_id],
        back_populates="friend",
    )
