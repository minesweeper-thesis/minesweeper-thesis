import asyncio
import random
import uuid

from backend.core.board import Board, DifficultyLevel, GenerationSettings
from backend.db.db import async_session_maker
from backend.repositories.board_repo import BoardRepository


def create_board_sync(rows=5, columns=5, mine_count=2) -> tuple[str, tuple[int, int]]:
    async def create():
        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                async with async_session_maker() as session:
                    await session.execute(text("PRAGMA busy_timeout=30000"))

                    repo = BoardRepository(session)
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
                    await repo.add_board(board)
                    return str(board.id), start_field
            except IntegrityError:
                if attempt == max_attempts - 1:
                    raise
                continue
        raise RuntimeError("Failed to create unique board after max attempts")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, create()).result()
    else:
        result = asyncio.run(create())

    return result


def create_board_from_full_board_sync(
    full_board: list[list[int]], start_field: tuple[int, int]
) -> str:
    async def create():
        from sqlalchemy import text

        async with async_session_maker() as session:
            await session.execute(text("PRAGMA busy_timeout=30000"))
            repo = BoardRepository(session)

            rows = len(full_board)
            columns = len(full_board[0])
            minefields = []
            for r in range(rows):
                for c in range(columns):
                    if full_board[r][c] == -1:
                        minefields.append((r, c))

            mine_count = len(minefields)
            difficulty = DifficultyLevel(
                rows=rows, columns=columns, mine_count=mine_count
            )

            board = Board(
                id=uuid.uuid4(),
                minefields=minefields,
                start_field=start_field,
                generation_settings=GenerationSettings(
                    type="random", settings=None, difficulty_level=difficulty
                ),
            )
            await repo.add_board(board)
            return str(board.id)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, create()).result()
    else:
        result = asyncio.run(create())

    return result


def create_game(
    client, rows=5, columns=5, mine_count=2, board_id: str | None = None
) -> str:
    if board_id is None:
        board_id, _ = create_board_sync(
            rows=rows, columns=columns, mine_count=mine_count
        )

    resp = client.post(
        "/api/game/single",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )
    assert resp.status_code == 200, f"Failed to create game: {resp.text}"
    return resp.json()["gameplay_id"]
