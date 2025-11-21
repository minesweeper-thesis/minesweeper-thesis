import enum
import uuid
from typing import Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Table,
    event,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from backend.core.singleplayer import SingleplayerGameplay
from backend.repositories.orm import Base

from .board_orm import BoardORM, DifficultyLevelORM
from .user_orm import UserORM


class GameStatusEnum(enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    finished = "finished"


class GameResultEnum(enum.Enum):
    win = "win"
    loss = "loss"


class GameModeEnum(enum.Enum):
    normal = "normal"
    hardcore = "hardcore"


class SingleplayerGameplayORM(Base):
    __tablename__ = "singleplayer_gameplays"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey(UserORM.id), index=True
    )
    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(BoardORM.id), index=True)
    time: Mapped[float] = mapped_column(default=0)
    used_hints: Mapped[bool] = mapped_column(default=False)
    status: Mapped[GameStatusEnum] = mapped_column(
        Enum(GameStatusEnum), default="not_started"
    )
    result: Mapped[Optional[GameResultEnum]] = mapped_column(Enum(GameResultEnum))
    revealed_cells: Mapped[list[tuple[int, int]]] = mapped_column(JSON, default=[])

    mode: Mapped[GameModeEnum] = mapped_column(Enum(GameModeEnum), default="normal")

    user: Mapped[Optional[UserORM]] = relationship(
        back_populates="singleplayer_gameplays"
    )
    board: Mapped[BoardORM] = relationship()

    def to_gameplay(self) -> "SingleplayerGameplay":
        return SingleplayerGameplay(
            id=self.id,
            board=self.board.to_board(),
            revealed_cells=self.revealed_cells,
            status=self.status.value,
            result=self.result.value if self.result else None,
            used_hints=self.used_hints,
            elapsed_time=self.time,
            mode=self.mode.value,
        )

    @staticmethod
    def from_gameplay(
        gameplay: "SingleplayerGameplay",
        board_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> "SingleplayerGameplayORM":
        return SingleplayerGameplayORM(
            id=gameplay.id,
            user_id=user_id,
            board_id=board_id,
            time=gameplay.elapsed_time,
            used_hints=gameplay.used_hints,
            status=gameplay.status,
            result=gameplay.result,
            mode=gameplay.game_mode,
            revealed_cells=[(i, j) for i, j, _ in gameplay.revealed],
        )


class MultiplayerSessionORM(Base):
    __tablename__ = "multiplayer_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    difficulty_level_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(DifficultyLevelORM.id), index=True
    )
    mode: Mapped[GameModeEnum] = mapped_column(Enum(GameModeEnum), default="normal")

    difficulty_level: Mapped[DifficultyLevelORM] = relationship()

    max_round_time: Mapped[float] = mapped_column()
    rounds_number: Mapped[int] = mapped_column()

    rounds: Mapped[list["MultiplayerRoundORM"]] = relationship(back_populates="session")
    players: Mapped[list["UserORM"]] = relationship(
        secondary="multiplayer_session_players"
    )


multiplayer_session_players = Table(
    "multiplayer_session_players",
    Base.metadata,
    Column("session_id", ForeignKey(MultiplayerSessionORM.id), primary_key=True),
    Column("user_id", ForeignKey(UserORM.id), primary_key=True),
)


class MultiplayerRoundORM(Base):
    __tablename__ = "multiplayer_rounds"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(MultiplayerSessionORM.id), primary_key=True
    )
    session: Mapped[MultiplayerSessionORM] = relationship(back_populates="rounds")

    round_number: Mapped[int] = mapped_column(primary_key=True)

    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(BoardORM.id), index=True)
    board: Mapped[BoardORM] = relationship()

    gameplays: Mapped[list["MultiplayerGameplayORM"]] = relationship(
        back_populates="round"
    )

    __table_args__ = (
        CheckConstraint("round_number >= 0", name="check_round_number_non_negative"),
    )


class MultiplayerGameplayORM(Base):
    __tablename__ = "multiplayer_gameplays"

    session_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    round_number: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(UserORM.id), primary_key=True, index=True
    )

    time: Mapped[float] = mapped_column(default=0)
    status: Mapped[GameStatusEnum] = mapped_column(
        Enum(GameStatusEnum), default="not_started"
    )
    result: Mapped[Optional[GameResultEnum]] = mapped_column(Enum(GameResultEnum))
    revealed_cells: Mapped[list[tuple[int, int]]] = mapped_column(JSON, default=[])

    user: Mapped[UserORM] = relationship()
    round: Mapped[MultiplayerRoundORM] = relationship(
        back_populates="gameplays", foreign_keys=[session_id, round_number]
    )

    __table_args__ = (
        ForeignKeyConstraint(
            [session_id, round_number],
            [MultiplayerRoundORM.session_id, MultiplayerRoundORM.round_number],
        ),
    )


@event.listens_for(Session, "before_flush")
def validate_rounds_count(session, flush_context, instances):
    """Validate that each session has exactly rounds_number rounds with correct numbering."""
    for obj in session.dirty | session.new:
        if isinstance(obj, MultiplayerSessionORM):
            if obj.rounds_number is not None:
                actual_rounds = len(obj.rounds)
                if actual_rounds > 0 and actual_rounds != obj.rounds_number:
                    raise ValueError(
                        f"Session must have exactly {obj.rounds_number} rounds, "
                        f"but has {actual_rounds}"
                    )

                if actual_rounds > 0:
                    round_numbers = {r.round_number for r in obj.rounds}
                    expected_numbers = set(range(obj.rounds_number))
                    if round_numbers != expected_numbers:
                        raise ValueError(
                            f"Round numbers must be 0 to {obj.rounds_number-1}, "
                            f"but got {sorted(round_numbers)}"
                        )

        if isinstance(obj, MultiplayerRoundORM):
            session_obj = obj.session
            if session_obj and session_obj.players:
                expected_players = len(session_obj.players)
                actual_gameplays = len(obj.gameplays)
                if actual_gameplays > 0 and actual_gameplays != expected_players:
                    raise ValueError(
                        f"Round must have gameplay for all {expected_players} players, "
                        f"but has {actual_gameplays} gameplays"
                    )

            if session_obj and session_obj.rounds_number is not None:
                if obj.round_number >= session_obj.rounds_number:
                    raise ValueError(
                        f"Round number {obj.round_number} must be < {session_obj.rounds_number}"
                    )

            if session_obj and obj.board:
                if obj.board.difficulty_level_id != session_obj.difficulty_level_id:
                    raise ValueError(
                        f"Round board must have same difficulty level as session "
                        f"(expected {session_obj.difficulty_level_id}, "
                        f"got {obj.board.difficulty_level_id})"
                    )


__all__ = [
    "SingleplayerGameplayORM",
    "MultiplayerGameplayORM",
    "MultiplayerSessionORM",
    "MultiplayerRoundORM",
    "GameStatusEnum",
    "GameResultEnum",
    "GameModeEnum",
]
