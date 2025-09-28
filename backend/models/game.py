import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from backend.models import Board, User


class Gameplay(Base):
    __tablename__ = "gameplay"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("board.id"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(nullable=False, default=0.0, index=True)
    time: Mapped[float] = mapped_column(nullable=False, index=True)
    used_prompts: Mapped[bool] = mapped_column(nullable=False, default=False)

    user: Mapped["User"] = relationship("User", back_populates="boards")
    board: Mapped["Board"] = relationship("Board", back_populates="gameplays")
