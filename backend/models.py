from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Friend(Base):
    __tablename__ = "friend"

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    friend_id = Column(Integer, ForeignKey("user.id"), primary_key=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friend_of")

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_friend"),
    )

class FriendInvitation(Base):
    __tablename__ = "friend_invitation"

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    friend_id = Column(Integer, ForeignKey("user.id"), primary_key=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="sent_invitations")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="received_invitations")

    __table_args__ = (
        CheckConstraint("user_id != friend_id", name="check_not_self_invite"),
    )

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    nickname = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    generatorsettings = Column(Text, nullable=False, index=True)

    boards = relationship("Gameplay", back_populates="user", cascade="all, delete")
    friends = relationship("Friend", foreign_keys=[Friend.user_id], back_populates="user")
    friend_of = relationship("Friend", foreign_keys=[Friend.friend_id], back_populates="friend")
    sent_invitations = relationship("FriendInvitation", foreign_keys=[FriendInvitation.user_id], back_populates="user")
    received_invitations = relationship("FriendInvitation", foreign_keys=[FriendInvitation.friend_id], back_populates="friend")

class BoardType(Base):
    __tablename__ = "board_type"

    id = Column(Integer, primary_key=True)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    mine_count = Column(Integer, nullable=False)
    start_field = Column(String, nullable=False)

    __table_args__ = (
        Index("rows", "columns", "mine_count", "start_field", name="ix_boardtype"),
        UniqueConstraint(
            "rows", "columns", "mine_count", "start_field", name="uq_boardtype_tuple"
        ),
    )

    boards = relationship("Board", back_populates="board_type")

class Board(Base):
    __tablename__ = "board"

    id = Column(Integer, primary_key=True)
    board_type_id = Column(
        Integer, ForeignKey("board_type.id"), nullable=False, index=True
    )
    minedfields = Column(Text, unique=True, nullable=False, index=True)

    board_type = relationship("BoardType", back_populates="boards")
    gameplays = relationship("Gameplay", back_populates="board")

class Gameplay(Base):
    __tablename__ = "gameplay"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    board_id = Column(Integer, ForeignKey("board.id"), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0.0, index=True)
    time = Column(Float, nullable=False, index=True)
    used_prompts = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="boards")
    board = relationship("Board", back_populates="gameplays")
