import uuid

from sqlalchemy import Boolean, Column, Float, ForeignKey, Uuid
from sqlalchemy.orm import relationship

from .base import Base


class Gameplay(Base):
    __tablename__ = "gameplay"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("user.id"), nullable=False, index=True)
    board_id = Column(Uuid, ForeignKey("board.id"), nullable=False, index=True)
    score = Column(Float, nullable=False, default=0.0, index=True)
    time = Column(Float, nullable=False, index=True)
    used_prompts = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="boards")
    board = relationship("Board", back_populates="gameplays")
