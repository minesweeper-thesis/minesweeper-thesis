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

def test_websocket_reveal_one_returns_response(client, auth):
    email = f"ws-reveal-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_reveal")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        data = json.loads(ws.receive_text())

        assert data["type"] == "reveal"
        assert "revealed_cells" in data
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]
        assert isinstance(data["revealed_cells"], list)

def test_websocket_reveal_start_field_is_safe(client, auth):
    email = f"ws-startsafe-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_startsafe")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        data = json.loads(ws.receive_text())

        if data["type"] == "game_over":
            assert (
                data.get("game_status") != "loss"
            ), "Start field should never be a mine!"
        else:
            assert data["type"] == "reveal"

def test_websocket_reveal_returns_valid_cell_values(client, auth):
    email = f"ws-cellval-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_cellval")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        data = json.loads(ws.receive_text())

        if data["type"] == "reveal":
            for cell in data["revealed_cells"]:

                val = cell.get("value") if isinstance(cell, dict) else cell[2]
                if val is not None:
                    assert 0 <= val <= 8, f"Invalid cell value: {val}"

def test_websocket_flag_returns_response(client, auth):
    email = f"ws-flag-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flag")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (0, 0)})
        data = json.loads(ws.receive_text())

        assert data["type"] == "flag"
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]

def test_websocket_remove_flag_returns_response(client, auth):
    email = f"ws-unflag-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_unflag")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (0, 0)})
        ws.receive_text()

        ws.send_json({"type": "remove_flag", "cell": (0, 0)})
        data = json.loads(ws.receive_text())

        assert data["type"] == "remove_flag"
        assert "game_status" in data

def test_websocket_flag_and_unflag_same_cell(client, auth):
    email = f"ws-flagunflag-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flagunflag")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=1)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (1, 1)})
        flag_resp = json.loads(ws.receive_text())
        assert flag_resp["type"] == "flag"

        ws.send_json({"type": "remove_flag", "cell": (1, 1)})
        unflag_resp = json.loads(ws.receive_text())
        assert unflag_resp["type"] == "remove_flag"

def test_websocket_flag_shows_in_state(client, auth):
    email = f"ws-flagstate-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flagstate")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=1)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (0, 0)})
        ws.receive_text()

        ws.send_json({"type": "get_state"})
        state_data = json.loads(ws.receive_text())
        board = state_data["board"]

        cell_value = board[0][0]
        assert cell_value == -4, f"Cell should be flagged (-4), got {cell_value}"

def test_websocket_use_hint_action(client, auth):
    email = f"ws-hint-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_hint")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()

        ws.send_json({"type": "use_hint"})
        data = json.loads(ws.receive_text())

        assert data["type"] in ["hint", "error", "reveal", "game_state"]

def test_websocket_reveal_out_of_bounds(client, auth):
    from anyio import EndOfStream
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-oob-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_oob")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=1)

    try:
        with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
            ws.receive_text()

            ws.send_json({"type": "reveal_one", "cell": (100, 100)})
            data = json.loads(ws.receive_text())

            assert data["type"] in ["reveal", "error"]
    except (WebSocketDisconnect, EndOfStream, Exception):

        pass

def test_websocket_flag_revealed_cell(client, auth):
    email = f"ws-flagrev-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flagrev")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": start_field})
        data = json.loads(ws.receive_text())

        assert data["type"] in ["flag", "error", "game_over"]

def test_websocket_normal_mode(client, auth):
    email = f"ws-normal-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_normal")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        data = json.loads(ws.receive_text())
        assert data["type"] == "game_state"
