import random
import uuid

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.board import Board, DifficultyLevel, GenerationSettings
from backend.repositories.board_repo import BoardRepository


async def _save_board(board: Board, session: AsyncSession):
    await session.execute(text("PRAGMA busy_timeout=30000"))
    repo = BoardRepository(session)
    await repo.add_board(board)


async def create_board(
    session: AsyncSession, rows=5, columns=5, mine_count=2
) -> tuple[str, tuple[int, int]]:
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            difficulty = DifficultyLevel(
                rows=rows, columns=columns, mine_count=mine_count
            )

            start_row = random.randint(0, rows - 1)
            start_col = random.randint(0, columns - 1)
            start_field = (start_row, start_col)

            all_cells = [
                (r, c)
                for r in range(rows)
                for c in range(columns)
                if (r, c) != start_field
            ]
            random.shuffle(all_cells)
            minefields = sorted(all_cells[:mine_count])

            board = Board(
                id=uuid.uuid4(),
                minefields=minefields,
                start_field=start_field,
                generation_settings=GenerationSettings(
                    type="random", settings=None, difficulty_level=difficulty
                ),
            )
            await _save_board(board, session)
            return str(board.id), start_field
        except IntegrityError:
            if attempt == max_attempts - 1:
                raise
            continue
    raise RuntimeError("Failed to create unique board after max attempts")


async def create_board_from_full_board(
    session: AsyncSession, full_board: list[list[int]], start_field: tuple[int, int]
) -> str:
    rows = len(full_board)
    columns = len(full_board[0])
    minefields = []
    for r in range(rows):
        for c in range(columns):
            if full_board[r][c] == -1:
                minefields.append((r, c))

    mine_count = len(minefields)
    difficulty = DifficultyLevel(rows=rows, columns=columns, mine_count=mine_count)

    board = Board(
        id=uuid.uuid4(),
        minefields=minefields,
        start_field=start_field,
        generation_settings=GenerationSettings(
            type="random", settings=None, difficulty_level=difficulty
        ),
    )
    await _save_board(board, session)
    return str(board.id)


async def create_game(
    client,
    rows=5,
    columns=5,
    mine_count=2,
    board_id: str | None = None,
    session: AsyncSession | None = None,
) -> str:
    if board_id is None:
        if session is None:
            raise ValueError("session is required if board_id is not provided")
        board_id, _ = await create_board(
            session, rows=rows, columns=columns, mine_count=mine_count
        )

    resp = await client.post(
        "/game/single",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )
    assert resp.status_code == 200, f"Failed to create game: {resp.text}"
    return resp.json()["gameplay_id"]
