import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Index, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .game_models import SingleplayerGameplay


class BoardType(Base):
    __tablename__ = "board_type"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rows: Mapped[int] = mapped_column()
    columns: Mapped[int] = mapped_column()
    mine_count: Mapped[int] = mapped_column()

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
        ForeignKey("board_type.id"), index=True
    )
    minefields: Mapped[BoardGrid] = mapped_column(JSON)
    start_field: Mapped[tuple[int, int]] = mapped_column(JSON)

    board_type: Mapped[BoardType] = relationship("BoardType", back_populates="boards")
    singleplayer_gameplays: Mapped[list["SingleplayerGameplay"]] = relationship(
        "SingleplayerGameplay", back_populates="board"
    )


@event.listens_for(Board.__table__, "after_create")
def create_postgres_unique_index(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        connection.execute(
            """
            CREATE UNIQUE INDEX uq_board_type_minefields 
            ON board (board_type_id, (minefields::text))
            """
        )
    else:
        connection.execute(
            """
            CREATE UNIQUE INDEX uq_board_type_minefields 
            ON board (board_type_id, minefields)
            """
        )
