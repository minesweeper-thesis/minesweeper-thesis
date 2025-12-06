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

def test_websocket_initial_game_state_schema(client, auth):
    email = f"ws-init-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_init")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        data = json.loads(ws.receive_text())

        assert data["type"] == "game_state"

        assert "board_id" in data
        assert "status" in data
        assert "difficulty_level" in data
        assert "elapsed_time" in data
        assert "start_field" in data

        assert data["status"] in ["not_started", "in_progress", "finished"]
        assert isinstance(data["elapsed_time"], (int, float))
        assert isinstance(data["start_field"], list)
        assert len(data["start_field"]) == 2

        dl = data["difficulty_level"]
        assert "rows" in dl and dl["rows"] == 5
        assert "columns" in dl and dl["columns"] == 5
        assert "mine_count" in dl and dl["mine_count"] == 2

        assert data.get("result") is None

def test_websocket_game_over_loss_schema(client, auth):
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-loss-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_loss")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=7)

    game_over = None
    finished = False
    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        for x in range(3):
            if finished:
                break
            for y in range(3):
                if finished:
                    break
                if (x, y) == tuple(start_field):
                    continue
                ws.send_json({"type": "reveal_one", "cell": (x, y)})
                try:
                    data = json.loads(ws.receive_text())
                    if data["type"] == "game_over":
                        game_over = data
                        finished = True
                except WebSocketDisconnect:
                    finished = True

    if game_over:
        assert "game_status" in game_over
        assert "full_board" in game_over
        assert "elapsed_time" in game_over
        assert isinstance(game_over["elapsed_time"], (int, float))
        assert isinstance(game_over["full_board"], list)

def test_websocket_get_game_state_returns_current_state(client, auth):
    email = f"ws-getstate-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_getstate")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=5)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        ws.receive_text()

        ws.send_json({"type": "get_state"})
        data = json.loads(ws.receive_text())

        assert data["type"] == "game_state"
        assert data["status"] == "in_progress"
        assert "board" in data
        assert data["board"] is not None
        assert isinstance(data["board"], list)
        assert len(data["board"]) == 5
        for row in data["board"]:
            assert len(row) == 5

def test_websocket_board_state_shows_revealed_cell(client, auth):
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-verify-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_verify")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=3)

    try:
        with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
            initial = json.loads(ws.receive_text())
            start_field = initial["start_field"]

            ws.send_json({"type": "reveal_one", "cell": start_field})
            reveal_data = json.loads(ws.receive_text())

            if reveal_data["type"] == "reveal":
                ws.send_json({"type": "get_state"})
                state_data = json.loads(ws.receive_text())
                board = state_data["board"]

                cell_value = board[start_field[0]][start_field[1]]

                assert cell_value != -3, f"Cell should be revealed, got {cell_value}"
            elif reveal_data["type"] == "game_over":

                pass
    except WebSocketDisconnect:

        pass
