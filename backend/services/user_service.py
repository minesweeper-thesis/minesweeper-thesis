import uuid

from sqlalchemy import select

from ..db import *
from ..models import *


async def save_gameplay(
    user_id: uuid.UUID,
    board_id: uuid.UUID,
    score: float,
    time: float,
    used_prompts: bool,
):
    async with async_session_maker() as db:
        gameplay = Gameplay(
            user_id=user_id,
            board_id=board_id,
            score=score,
            time=time,
            used_prompts=used_prompts,
        )
        db.add(gameplay)
        await db.commit()
        await db.refresh(gameplay)
        return gameplay


async def get_gameplays(user_id: uuid.UUID):
    async with async_session_maker() as db:
        stmt = select(Gameplay).where(Gameplay.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()
