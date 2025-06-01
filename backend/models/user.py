from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import UUID, CheckConstraint, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Friend(Base):
    __tablename__ = "friend"

    user_id = Column(UUID, ForeignKey("user.id"), primary_key=True)
    friend_id = Column(UUID, ForeignKey("user.id"), primary_key=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friend_of")

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_friend"),
    )


class FriendInvitation(Base):
    __tablename__ = "friend_invitation"

    user_id = Column(UUID, ForeignKey("user.id"), primary_key=True)
    friend_id = Column(UUID, ForeignKey("user.id"), primary_key=True)

    user = relationship(
        "User", foreign_keys=[user_id], back_populates="sent_invitations"
    )
    friend = relationship(
        "User", foreign_keys=[friend_id], back_populates="received_invitations"
    )

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_invite"),
    )


class User(Base, SQLAlchemyBaseUserTableUUID):
    __tablename__ = "user"

    email = Column(String, unique=True, nullable=False, index=True)
    nickname = Column(String, unique=True, nullable=False, index=True)
    generator_settings = Column(Text, nullable=False, index=True)

    boards = relationship("Gameplay", back_populates="user", cascade="all, delete")
    friends = relationship(
        "Friend", foreign_keys=[Friend.user_id], back_populates="user"
    )
    friend_of = relationship(
        "Friend", foreign_keys=[Friend.friend_id], back_populates="friend"
    )
    sent_invitations = relationship(
        "FriendInvitation",
        foreign_keys=[FriendInvitation.user_id],
        back_populates="user",
    )
    received_invitations = relationship(
        "FriendInvitation",
        foreign_keys=[FriendInvitation.friend_id],
        back_populates="friend",
    )
