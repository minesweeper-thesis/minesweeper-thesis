import random
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.board import Board, DifficultyLevel, GenerationSettings
from backend.tests.conftest import create_or_get_board, generate_board_data


async def create_board(
    session: AsyncSession, rows=5, columns=5, mine_count=2
) -> tuple[str, tuple[int, int]]:
    difficulty = DifficultyLevel(rows=rows, columns=columns, mine_count=mine_count)
    minefields, start_field = generate_board_data(rows, columns, mine_count)

    board = await create_or_get_board(
        difficulty=difficulty,
        minefields=minefields,
        start_field=start_field,
        generation_settings=GenerationSettings(
            type="random", settings=None, difficulty_level=difficulty
        ),
    )
    return str(board.id), board.start_field


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

    board = await create_or_get_board(
        difficulty=difficulty,
        minefields=minefields,
        start_field=start_field,
        generation_settings=GenerationSettings(
            type="random", settings=None, difficulty_level=difficulty
        ),
    )
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
