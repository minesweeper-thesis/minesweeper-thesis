import uuid
from dataclasses import asdict

from sqlalchemy import (
    JSON,
    ForeignKey,
    Index,
    Text,
    TypeDecorator,
    UniqueConstraint,
    event,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import func

from backend.core.board import (
    Board,
    DifficultyLevel,
    GenerationSettings,
    GeneratorParams,
    Minefields,
)
from backend.repositories.orm import Base


class MinefieldsColumn(TypeDecorator):
    impl = JSON
    cache_ok = True

    @property
    def comparator_factory(self):
        type_self = self

        class Comparator(TypeDecorator.Comparator):
            def __eq__(self, other):
                import json

                processed_value = type_self.process_bind_param(other, None)  # type: ignore
                json_str = json.dumps(processed_value, sort_keys=True)
                return func.cast(self.expr, Text) == json_str

        return Comparator

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return [list(coord) for coord in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return [tuple(coord) for coord in value]


class GenerationSettingsColumn(TypeDecorator):
    impl = JSON
    cache_ok = True

    @property
    def comparator_factory(self):
        type_self = self

        class Comparator(TypeDecorator.Comparator):
            def __eq__(self, other):
                import json

                processed_value = type_self.process_bind_param(other, None)  # type: ignore
                json_str = json.dumps(processed_value, sort_keys=True)
                return func.cast(self.expr, Text) == json_str

        return Comparator

    def process_bind_param(self, value, dialect):
        if not isinstance(value, GenerationSettings):
            return None
        return asdict(value)

    def process_result_value(self, value, dialect):
        if not isinstance(value, dict):
            return None
        settings_dict = value["settings"]
        if settings_dict is not None:
            settings_dict["heuristic_args"] = tuple(settings_dict["heuristic_args"])
            settings = GeneratorParams(**settings_dict)
        else:
            settings = None

        return GenerationSettings(
            type=value["type"],
            difficulty_level=DifficultyLevel(**value["difficulty_level"]),
            settings=settings,
        )


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
    minefields: Mapped[Minefields] = mapped_column(MinefieldsColumn)
    start_field: Mapped[tuple[int, int]] = mapped_column(JSON)
    generation_settings: Mapped[GenerationSettings] = mapped_column(
        GenerationSettingsColumn
    )

    difficulty_level_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(DifficultyLevelORM.id), index=True
    )

    difficulty_level: Mapped[DifficultyLevelORM] = relationship(back_populates="boards")

    __table_args__ = (Index("uq_difficulty_level_minefields", difficulty_level_id),)

    def to_board(self) -> Board:
        return Board(
            id=self.id,
            minefields=self.minefields,
            start_field=self.start_field,
            generation_settings=self.generation_settings,
        )

    @staticmethod
    def from_board(board: Board, difficulty_level_id: uuid.UUID) -> "BoardORM":
        return BoardORM(
            id=board.id,
            difficulty_level_id=difficulty_level_id,
            minefields=board.minefields,
            start_field=board.start_field,
            generation_settings=board.generation_settings,
        )


@event.listens_for(BoardORM.__table__, "after_create")
def _create_postgres_unique_index(target, connection, **kw):
    connection.execute(text("DROP INDEX IF EXISTS uq_difficulty_level_minefields"))
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
