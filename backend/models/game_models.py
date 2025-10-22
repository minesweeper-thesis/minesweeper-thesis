import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from backend.models import Board, User


class Gameplay(Base):
    __tablename__ = "gameplay"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("user.id"), nullable=True, index=True
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("board.id"), nullable=False, index=True
    )
    time: Mapped[Optional[float]] = mapped_column(nullable=True, index=True)
    used_prompts: Mapped[Optional[bool]] = mapped_column(nullable=True, default=False)
    won: Mapped[Optional[bool]] = mapped_column(nullable=True, index=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="boards")
    board: Mapped["Board"] = relationship("Board", back_populates="gameplays")
