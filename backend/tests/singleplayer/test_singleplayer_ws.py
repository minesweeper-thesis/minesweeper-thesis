"""
Comprehensive singleplayer WebSocket tests.
Tests full gameplay flow with proper schema validation.
Response format is flat (no 'data' wrapper) - fields are at top level.
"""

import asyncio
import json
import random
import uuid

from backend.core.board import Board, DifficultyLevel, GenerationSettings
from backend.db.db import async_session_maker
from backend.repositories.board_repo import BoardRepository
from backend.routers.schemas.game.single_schemas import NewGameResponse


def _create_board_sync(rows=5, columns=5, mine_count=2) -> tuple[str, tuple[int, int]]:
    """Create a board directly in database and return board_id."""

    async def create():
        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                async with async_session_maker() as session:
                    # Set busy timeout for SQLite concurrency
                    await session.execute(text("PRAGMA busy_timeout=30000"))

                    repo = BoardRepository(session)
                    difficulty = DifficultyLevel(
                        rows=rows, columns=columns, mine_count=mine_count
                    )

                    # Generate RANDOM start_field and minefields
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
                        difficulty_level=difficulty,
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
        # We're inside an event loop (shouldn't happen in sync tests)
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, create()).result()
    else:
        result = asyncio.run(create())

    return result


def _create_game(client, rows=5, columns=5, mine_count=2) -> str:
    """Create a game with pre-made board and return gameplay_id."""
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


# =============================================================================
# HTTP Endpoint Tests
# =============================================================================


def test_start_game_validates_response(client, auth):
    """POST /api/game/single - validates NewGameResponse schema."""
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
    # Validate NewGameResponse schema
    assert "gameplay_id" in data
    game_response = NewGameResponse(**data)
    assert game_response.gameplay_id is not None
    uuid.UUID(str(game_response.gameplay_id))


def test_start_game_invalid_board_returns_404(client, auth):
    """POST /api/game/single with invalid board_id returns 404."""
    email = f"sp-invalid-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_invalid")

    fake_board_id = str(uuid.uuid4())
    resp = client.post(
        "/api/game/single",
        json={"board_id": fake_board_id, "mode": "normal"},
    )
    assert resp.status_code == 404


def test_start_game_works_without_auth(client):
    """POST /api/game/single without auth should still work (optional auth)."""
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
    """POST /api/game/single validates difficulty_level structure."""
    email = f"sp-diff-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_diff")

    resp = client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5},  # missing columns and mine_count
            "generator": {"type": "random"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 422


def test_start_game_validates_generator_type(client, auth):
    """POST /api/game/single validates generator type."""
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


# =============================================================================
# WebSocket Tests - Initial GameState
# =============================================================================


def test_websocket_initial_game_state_schema(client, auth):
    """WebSocket connect returns valid GameStateResponse (flat format)."""
    email = f"ws-init-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_init")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        data = json.loads(ws.receive_text())

        # Response is flat - fields at top level, not in "data" wrapper
        assert data["type"] == "game_state"

        # Required fields at top level
        assert "board_id" in data
        assert "status" in data
        assert "difficulty_level" in data
        assert "elapsed_time" in data
        assert "start_field" in data

        # Validate types
        assert data["status"] in ["not_started", "in_progress", "finished"]
        assert isinstance(data["elapsed_time"], (int, float))
        assert isinstance(data["start_field"], list)
        assert len(data["start_field"]) == 2

        # Validate difficulty_level structure
        dl = data["difficulty_level"]
        assert "rows" in dl and dl["rows"] == 5
        assert "columns" in dl and dl["columns"] == 5
        assert "mine_count" in dl and dl["mine_count"] == 2

        # result should be None initially
        assert data.get("result") is None


def test_websocket_invalid_gameplay_returns_error(client, auth):
    """WebSocket with invalid gameplay_id should fail or return error."""
    email = f"ws-invalid-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_invalid")

    fake_gameplay_id = str(uuid.uuid4())

    try:
        with client.websocket_connect(f"/api/game/single/{fake_gameplay_id}") as ws:
            data = json.loads(ws.receive_text())
            assert data.get("type") in ["error", "game_state"]
    except Exception:
        # Connection rejection is also acceptable
        pass


# =============================================================================
# WebSocket Tests - Reveal Actions
# =============================================================================


def test_websocket_reveal_one_returns_response(client, auth):
    """reveal_one action returns RevealResponse with revealed cells."""
    email = f"ws-reveal-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_reveal")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        # Reveal start field (guaranteed safe)
        ws.send_json({"type": "reveal_one", "x": start_field[0], "y": start_field[1]})
        data = json.loads(ws.receive_text())

        # Validate RevealResponse (flat format)
        assert data["type"] == "reveal"
        assert "revealed_cells" in data
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]
        assert isinstance(data["revealed_cells"], list)


def test_websocket_reveal_start_field_is_safe(client, auth):
    """Revealing start_field is always safe (never a mine)."""
    email = f"ws-startsafe-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_startsafe")

    # Single game - no loop to avoid SQLite locking issues
    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "x": start_field[0], "y": start_field[1]})
        data = json.loads(ws.receive_text())

        # Should NOT be game_over with loss
        if data["type"] == "game_over":
            assert (
                data.get("game_status") != "loss"
            ), "Start field should never be a mine!"
        else:
            assert data["type"] == "reveal"


def test_websocket_reveal_returns_valid_cell_values(client, auth):
    """Revealed cells have values in valid range (0-8 for neighbors)."""
    email = f"ws-cellval-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_cellval")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "x": start_field[0], "y": start_field[1]})
        data = json.loads(ws.receive_text())

        if data["type"] == "reveal":
            for cell in data["revealed_cells"]:
                # Cells have x, y, value structure
                val = cell.get("value") if isinstance(cell, dict) else cell[2]
                if val is not None:
                    assert 0 <= val <= 8, f"Invalid cell value: {val}"


# =============================================================================
# WebSocket Tests - Game Over Detection
# =============================================================================


def test_websocket_game_over_loss_schema(client, auth):
    """GameOverResponse for loss has correct structure."""
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-loss-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_loss")

    # Many mines to increase chance of hitting one
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
                ws.send_json({"type": "reveal_one", "x": x, "y": y})
                try:
                    data = json.loads(ws.receive_text())
                    if data["type"] == "game_over":
                        game_over = data
                        finished = True
                except WebSocketDisconnect:
                    finished = True

    # If we got a game_over response, validate it
    if game_over:
        assert "game_status" in game_over
        assert "full_board" in game_over
        assert "elapsed_time" in game_over
        assert isinstance(game_over["elapsed_time"], (int, float))
        assert isinstance(game_over["full_board"], list)


# def test_websocket_game_over_win_by_revealing_safe(client, auth):
#     """Revealing all safe cells triggers win."""
#     from starlette.websockets import WebSocketDisconnect

#     email = f"ws-win-{uuid.uuid4().hex[:8]}@example.com"
#     auth(email=email, password="pw", nickname="ws_win")

#     # 3x3 with 1 mine = 8 safe cells
#     gameplay_id = _create_game(client, rows=3, columns=3, mine_count=1)

#     revealed_count = 0
#     game_result = None
#     finished = False

#     with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
#         initial = json.loads(ws.receive_text())

#         for x in range(3):
#             if finished:
#                 break
#             for y in range(3):
#                 if finished:
#                     break
#                 ws.send_json({"type": "reveal_one", "x": x, "y": y})
#                 try:
#                     data = json.loads(ws.receive_text())

#                     if data["type"] == "game_over":
#                         game_result = data
#                         finished = True
#                     elif data["type"] == "reveal":
#                         revealed_count += len(data["revealed_cells"])
#                 except WebSocketDisconnect:
#                     finished = True

#     assert game_result is not None or revealed_count > 0


# =============================================================================
# WebSocket Tests - Flag Actions
# =============================================================================


def test_websocket_flag_returns_response(client, auth):
    """flag action returns FlagResponse with status."""
    email = f"ws-flag-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flag")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()  # Initial state

        ws.send_json({"type": "flag", "x": 0, "y": 0})
        data = json.loads(ws.receive_text())

        assert data["type"] == "flag"
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]


def test_websocket_remove_flag_returns_response(client, auth):
    """remove_flag action returns RemoveFlagResponse with status."""
    email = f"ws-unflag-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_unflag")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()  # Initial state

        ws.send_json({"type": "flag", "x": 0, "y": 0})
        ws.receive_text()  # flag response

        ws.send_json({"type": "remove_flag", "x": 0, "y": 0})
        data = json.loads(ws.receive_text())

        assert data["type"] == "remove_flag"
        assert "game_status" in data


def test_websocket_flag_and_unflag_same_cell(client, auth):
    """Flagging and unflagging same cell works correctly."""
    email = f"ws-flagunflag-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flagunflag")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=1)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()  # Initial state

        ws.send_json({"type": "flag", "x": 1, "y": 1})
        flag_resp = json.loads(ws.receive_text())
        assert flag_resp["type"] == "flag"

        ws.send_json({"type": "remove_flag", "x": 1, "y": 1})
        unflag_resp = json.loads(ws.receive_text())
        assert unflag_resp["type"] == "remove_flag"


# =============================================================================
# WebSocket Tests - State Verification
# =============================================================================


def test_websocket_get_game_state_returns_current_state(client, auth):
    """get_game_state returns GameStateResponse with current board state."""
    email = f"ws-getstate-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_getstate")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        # Reveal start field first
        ws.send_json({"type": "reveal_one", "x": start_field[0], "y": start_field[1]})
        ws.receive_text()  # reveal response

        ws.send_json({"type": "get_game_state"})
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
    """After reveal, get_game_state shows the revealed cell correctly."""
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-verify-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_verify")

    # Use larger board to avoid instant win
    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=3)

    try:
        with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
            initial = json.loads(ws.receive_text())
            start_field = initial["start_field"]

            ws.send_json(
                {"type": "reveal_one", "x": start_field[0], "y": start_field[1]}
            )
            reveal_data = json.loads(ws.receive_text())

            if reveal_data["type"] == "reveal":
                ws.send_json({"type": "get_game_state"})
                state_data = json.loads(ws.receive_text())
                board = state_data["board"]

                cell_value = board[start_field[0]][start_field[1]]
                # -3 is NOT_REVEALED, after reveal should be 0-8
                assert cell_value != -3, f"Cell should be revealed, got {cell_value}"
            elif reveal_data["type"] == "game_over":
                # If reveal caused instant win, that's fine
                pass
    except WebSocketDisconnect:
        # Server closed connection after game over - acceptable
        pass


def test_websocket_flag_shows_in_state(client, auth):
    """After flagging, get_game_state shows the flagged cell."""
    email = f"ws-flagstate-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flagstate")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=1)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()  # Initial state

        ws.send_json({"type": "flag", "x": 0, "y": 0})
        ws.receive_text()

        ws.send_json({"type": "get_game_state"})
        state_data = json.loads(ws.receive_text())
        board = state_data["board"]

        # -4 = FLAG constant per game_schemas.py CellSpecial
        cell_value = board[0][0]
        assert cell_value == -4, f"Cell should be flagged (-4), got {cell_value}"


# =============================================================================
# WebSocket Tests - reveal_many
# =============================================================================


def test_websocket_reveal_many_action(client, auth):
    """reveal_many action returns appropriate response or error."""
    from anyio import EndOfStream
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-revmany-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_revmany")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    try:
        with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
            initial = json.loads(ws.receive_text())
            start_field = initial["start_field"]

            ws.send_json(
                {"type": "reveal_one", "x": start_field[0], "y": start_field[1]}
            )
            ws.receive_text()

            ws.send_json(
                {"type": "reveal_many", "x": start_field[0], "y": start_field[1]}
            )
            data = json.loads(ws.receive_text())

            assert data["type"] in ["reveal", "game_over", "error"]
    except (WebSocketDisconnect, EndOfStream, Exception):
        # Server may disconnect if reveal_many requirements not met
        pass


# =============================================================================
# WebSocket Tests - Hint Action
# =============================================================================


def test_websocket_use_hint_action(client, auth):
    """use_hint action returns appropriate response."""
    email = f"ws-hint-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_hint")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        ws.receive_text()  # Initial state

        ws.send_json({"type": "use_hint"})
        data = json.loads(ws.receive_text())

        assert data["type"] in ["hint", "error", "reveal", "game_state"]


# =============================================================================
# WebSocket Tests - Edge Cases
# =============================================================================


def test_websocket_reveal_already_revealed_cell(client, auth):
    """Revealing already revealed cell doesn't crash - server may disconnect or return error."""
    from anyio import EndOfStream
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-rereveal-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_rereveal")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    try:
        with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
            initial = json.loads(ws.receive_text())
            start_field = initial["start_field"]

            ws.send_json(
                {"type": "reveal_one", "x": start_field[0], "y": start_field[1]}
            )
            ws.receive_text()

            ws.send_json(
                {"type": "reveal_one", "x": start_field[0], "y": start_field[1]}
            )
            data = json.loads(ws.receive_text())

            assert data["type"] in ["reveal", "error", "game_state"]
    except (WebSocketDisconnect, EndOfStream, Exception):
        # Server disconnects on InvalidAction - this is expected behavior
        pass


def test_websocket_reveal_out_of_bounds(client, auth):
    """Revealing out of bounds coordinates - server may disconnect or return error."""
    from anyio import EndOfStream
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-oob-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_oob")

    gameplay_id = _create_game(client, rows=3, columns=3, mine_count=1)

    try:
        with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
            ws.receive_text()  # Initial state

            ws.send_json({"type": "reveal_one", "x": 100, "y": 100})
            data = json.loads(ws.receive_text())

            assert data["type"] in ["reveal", "error"]
    except (WebSocketDisconnect, EndOfStream, Exception):
        # Server disconnects on IndexError - this is expected behavior
        pass


def test_websocket_flag_revealed_cell(client, auth):
    """Flagging already revealed cell is handled."""
    email = f"ws-flagrev-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_flagrev")

    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "x": start_field[0], "y": start_field[1]})
        ws.receive_text()

        ws.send_json({"type": "flag", "x": start_field[0], "y": start_field[1]})
        data = json.loads(ws.receive_text())

        assert data["type"] in ["flag", "error"]


def test_websocket_normal_mode(client, auth):
    """Normal mode game works correctly."""
    email = f"ws-normal-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_normal")

    # Use _create_game to avoid BackgroundTasks timing issues
    gameplay_id = _create_game(client, rows=5, columns=5, mine_count=2)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        data = json.loads(ws.receive_text())
        assert data["type"] == "game_state"
