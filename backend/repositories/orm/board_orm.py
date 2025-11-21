import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Index, UniqueConstraint, event, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.board import Board, DifficultyLevel, Minefields
from backend.repositories.orm import Base

if TYPE_CHECKING:
    from .game_orm import MultiplayerGameplayORM, SingleplayerGameplayORM


class DifficultyLevelORM(Base):
    __tablename__ = "difficulty_levels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rows: Mapped[int] = mapped_column()
    columns: Mapped[int] = mapped_column()
    mine_count: Mapped[int] = mapped_column()

    boards: Mapped[list["BoardORM"]] = relationship(back_populates="difficulty_level")

    __table_args__ = (
        Index("ix_difficulty_level", "rows", "columns", "mine_count"),
        UniqueConstraint(
            "rows", "columns", "mine_count", name="uq_difficulty_level_tuple"
        ),
    )

    def to_difficulty_level(self) -> DifficultyLevel:
        return DifficultyLevel(
            rows=self.rows,
            columns=self.columns,
            mine_count=self.mine_count,
        )


class BoardORM(Base):
    __tablename__ = "boards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    minefields: Mapped[Minefields] = mapped_column(JSON)
    start_field: Mapped[tuple[int, int]] = mapped_column(JSON)

    difficulty_level_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(DifficultyLevelORM.id), index=True
    )

    difficulty_level: Mapped[DifficultyLevelORM] = relationship(back_populates="boards")

    def to_board(self) -> Board:
        difficulty_level = self.difficulty_level.to_difficulty_level()
        return Board(
            id=self.id,
            difficulty_level=difficulty_level,
            minefields=self.minefields,
            start_field=self.start_field,
        )

    @staticmethod
    def from_board(board: Board, difficulty_level_id: uuid.UUID) -> "BoardORM":
        return BoardORM(
            id=board.id,
            difficulty_level_id=difficulty_level_id,
            minefields=board.minefields,
            start_field=board.start_field,
        )


@event.listens_for(BoardORM.__table__, "after_create")
def _create_postgres_unique_index(target, connection, **kw):
    if connection.dialect.name == "postgresql":
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX uq_difficulty_level_minefields
                ON boards (difficulty_level_id, (minefields::text))
                """
            )
        )
    else:
        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX uq_difficulty_level_minefields
                ON boards (difficulty_level_id, minefields)
                """
            )
        )


__all__ = ["BoardORM", "DifficultyLevelORM"]
