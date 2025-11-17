from sqlalchemy import select

from backend.core.board import DifficultyLevel
from backend.repositories.orm.board_orm import DifficultyLevelORM


async def _get_difficulty_level_orm(
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
