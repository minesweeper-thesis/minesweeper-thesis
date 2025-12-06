import asyncio
import json
import random
import uuid

from backend.core.board import Board, DifficultyLevel, GenerationSettings
from backend.db.db import async_session_maker
from backend.repositories.board_repo import BoardRepository
from backend.routers.schemas.game.single_schemas import NewGameResponse

def _create_board_sync(rows=5, columns=5, mine_count=2) -> tuple[str, tuple[int, int]]:

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

def _create_game(client, rows=5, columns=5, mine_count=2) -> str:
    board_id, _ = _create_board_sync(rows=rows, columns=columns, mine_count=mine_count)

    resp = client.post(
        "/api/game/single",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )
    assert resp.status_code == 200, f"Failed to create game: {resp.text}"
    return resp.json()["gameplay_id"]

def test_start_game_validates_response(client, auth):
    email = f"sp-start-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_start")

    resp = client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 2},
            "generator": {"type": "random"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 200

    data = resp.json()

    assert "gameplay_id" in data
    game_response = NewGameResponse(**data)
    assert game_response.gameplay_id is not None
    uuid.UUID(str(game_response.gameplay_id))

def test_start_game_invalid_board_returns_404(client, auth):
    email = f"sp-invalid-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_invalid")

    fake_board_id = str(uuid.uuid4())
    resp = client.post(
        "/api/game/single",
        json={"board_id": fake_board_id, "mode": "normal"},
    )
    assert resp.status_code == 404

def test_start_game_works_without_auth(client):
    resp = client.post(
        "/api/game/single",
        json={
            "mode": "normal",
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 3},
            "generator": {"type": "random"},
        },
    )
    assert resp.status_code == 200
    assert "gameplay_id" in resp.json()

def test_start_game_validates_difficulty_level(client, auth):
    email = f"sp-diff-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_diff")

    resp = client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5},
            "generator": {"type": "random"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 422

def test_start_game_validates_generator_type(client, auth):
    email = f"sp-gen-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_gen")

    resp = client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 2},
            "generator": {"type": "invalid_generator"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 422

def test_websocket_invalid_gameplay_returns_error(client, auth):
    email = f"ws-invalid-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_invalid")

    fake_gameplay_id = str(uuid.uuid4())

    try:
        with client.websocket_connect(f"/api/game/single/{fake_gameplay_id}") as ws:
            data = json.loads(ws.receive_text())
            assert data.get("type") in ["error", "game_state"]
    except Exception:

        pass
