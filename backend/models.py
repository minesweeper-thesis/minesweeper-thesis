from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, CheckConstraint,
    UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    nickname = Column(String, nullable=False)
    password = Column(String, nullable=False)
    generatorsettings = Column(String)

    boards = relationship('Gameplay', back_populates='user', cascade='all, delete')


class Friend(Base):
    __tablename__ = 'friends'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    __table_args__ = (
        CheckConstraint('user_id != friend_id', name='check_not_self_friend'),
    )


class FriendInvitation(Base):
    __tablename__ = 'friend_invitations'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    __table_args__ = (
        CheckConstraint('user_id != friend_id', name='check_not_self_invite'),
    )


class BoardType(Base):
    __tablename__ = 'board_types'

    id = Column(Integer, primary_key=True)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    mine_count = Column(Integer, nullable=False)
    start_field = Column(String, nullable=False)

    __table_args__ = (
        Index('ix_boardtype_unique', 'rows', 'columns', 'mine_count', 'start_field'),
    )

    boards = relationship('Board', back_populates='board_type')


class Board(Base):
    __tablename__ = 'boards'

    id = Column(Integer, primary_key=True)
    boardtype_id = Column(Integer, ForeignKey('board_types.id'), nullable=False)
    minedfields = Column(String, nullable=False)

    __table_args__ = (
        Index('ix_boardtype_id', 'boardtype_id'),
        Index('ix_minedfields', 'minedfields'),
    )

    board_type = relationship('BoardType', back_populates='boards')
    gameplays = relationship('Gameplay', back_populates='board')


class Gameplay(Base):
    __tablename__ = 'gameplays'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    board_id = Column(Integer, ForeignKey('boards.id'), nullable=False)
    score = Column(Float, nullable=False)
    time = Column(Float, nullable=False)
    used_prompts = Column(Boolean, nullable=False, default=False)

    user = relationship('User', back_populates='boards')
    board = relationship('Board', back_populates='gameplays')
