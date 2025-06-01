from sqlalchemy import (
    UUID,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


class BoardType(Base):
    __tablename__ = "board_type"

    id = Column(UUID, primary_key=True)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    mine_count = Column(Integer, nullable=False)
    start_field = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_boardtype", "mine_count", "start_field"),
        UniqueConstraint("mine_count", "start_field", name="uq_boardtype_tuple"),
    )

    boards = relationship("Board", back_populates="board_type")


class Board(Base):
    __tablename__ = "board"

    id = Column(UUID, primary_key=True)
    board_type_id = Column(
        UUID, ForeignKey("board_type.id"), nullable=False, index=True
    )
    minedfields = Column(Text, unique=True, nullable=False, index=True)

    board_type = relationship("BoardType", back_populates="boards")
    gameplays = relationship("Gameplay", back_populates="board")
