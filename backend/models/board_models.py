import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .game_models import Gameplay


class BoardType(Base):
    __tablename__ = "board_type"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rows: Mapped[int] = mapped_column(nullable=False)
    columns: Mapped[int] = mapped_column(nullable=False)
    mine_count: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_boardtype", "rows", "columns", "mine_count"),
        UniqueConstraint("rows", "columns", "mine_count", name="uq_boardtype_tuple"),
    )

    boards: Mapped[list["Board"]] = relationship("Board", back_populates="board_type")


type BoardGrid = list[tuple[int, int]]


class Board(Base):
    __tablename__ = "board"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("board_type.id"), nullable=False, index=True
    )
    minefields: Mapped[BoardGrid] = mapped_column(JSON, unique=True, nullable=False)

    board_type: Mapped[BoardType] = relationship("BoardType", back_populates="boards")
    gameplays: Mapped[list["Gameplay"]] = relationship(
        "Gameplay", back_populates="board"
    )
