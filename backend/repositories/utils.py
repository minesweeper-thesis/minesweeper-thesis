import functools
from typing import Sequence

from sqlalchemy import select

from backend.core.board import DifficultyLevel
from backend.core.user import User
from backend.repositories.orm.board_orm import DifficultyLevelORM
from backend.repositories.orm.user_orm import UserORM


async def get_difficulty_level_orm(
    self, difficulty_level: DifficultyLevel
) -> DifficultyLevelORM:
    rows = difficulty_level.rows
    columns = difficulty_level.columns
    mine_count = difficulty_level.mine_count

    stmt = select(DifficultyLevelORM).where(
        DifficultyLevelORM.rows == rows,
        DifficultyLevelORM.columns == columns,
        DifficultyLevelORM.mine_count == mine_count,
    )
    result = await self.session.execute(stmt)
    difficulty_level = result.scalar_one_or_none()

    if difficulty_level is None:
        difficulty_level = DifficultyLevelORM(
            rows=rows, columns=columns, mine_count=mine_count
        )
        self.session.add(difficulty_level)
        await self.session.commit()
        await self.session.refresh(difficulty_level)

    return difficulty_level


async def _transformer(self, items: Sequence[UserORM]) -> list[User]:
    result = []
    for user in items:
        is_online = await self.is_user_online(user.id)
        result.append(user.to_user(is_online))
    return result


get_users_transformer = lambda self: functools.partial(_transformer, self)
