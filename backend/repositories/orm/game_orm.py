import enum
import uuid
from typing import Optional

from sqlalchemy import JSON, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.singleplayer import SingleplayerGameplay
from backend.repositories.orm import Base

from .board_orm import BoardORM
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


class MultiplayerGameplayORM(Base):
    __tablename__ = "multiplayer_gameplays"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(BoardORM.id), index=True)

    board: Mapped[BoardORM] = relationship()


__all__ = [
    "SingleplayerGameplayORM",
    "MultiplayerGameplayORM",
    "GameStatusEnum",
    "GameResultEnum",
    "GameModeEnum",
]
