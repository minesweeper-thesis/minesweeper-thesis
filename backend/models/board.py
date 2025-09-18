import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .game import Gameplay


class BoardType(Base):
    __tablename__ = "board_type"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rows: Mapped[int] = mapped_column(nullable=False)
    columns: Mapped[int] = mapped_column(nullable=False)
    mine_count: Mapped[int] = mapped_column(nullable=False)
    start_field: Mapped[str] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_boardtype", "mine_count", "start_field"),
        UniqueConstraint("mine_count", "start_field", name="uq_boardtype_tuple"),
    )

    boards: Mapped[list["Board"]] = relationship("Board", back_populates="board_type")


class Board(Base):
    __tablename__ = "board"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("board_type.id"), nullable=False, index=True
    )
    minedfields: Mapped[str] = mapped_column(unique=True, nullable=False)

    board_type: Mapped[BoardType] = relationship("BoardType", back_populates="boards")
    gameplays: Mapped[list["Gameplay"]] = relationship(
        "Gameplay", back_populates="board"
    )
