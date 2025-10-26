import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.game.game import GameResult, GameStatus

from .base import Base

if TYPE_CHECKING:
    from backend.models import Board, User


class SingleplayerGameplay(Base):
    __tablename__ = "singleplayer_gameplay"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user.id"), index=True
    )
    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("board.id"), index=True)
    time: Mapped[float] = mapped_column(default=0)
    used_hints: Mapped[bool] = mapped_column(default=False)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus), default=GameStatus.not_started
    )
    result: Mapped[Optional[GameResult]] = mapped_column(Enum(GameResult))
    revealed_cells: Mapped[list[tuple[int, int]]] = mapped_column(JSON, default=[])

    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="singleplayer_gameplays"
    )
    board: Mapped["Board"] = relationship(
        "Board", back_populates="singleplayer_gameplays"
    )
