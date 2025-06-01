from sqlalchemy import UUID, Boolean, Column, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Gameplay(Base):
    __tablename__ = "gameplay"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("user.id"), nullable=False, index=True)
    board_id = Column(UUID, ForeignKey("board.id"), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0.0, index=True)
    time = Column(Float, nullable=False, index=True)
    used_prompts = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="boards")
    board = relationship("Board", back_populates="gameplays")
