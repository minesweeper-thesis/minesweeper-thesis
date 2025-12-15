import json
import uuid

import pytest

from backend.tests.singleplayer.helpers import create_game


@pytest.mark.asyncio
async def test_websocket_initial_game_state_schema(client, auth_ws, ws_client, session):
    email = f"ws-init-{uuid.uuid4().hex[:8]}@example.com"
    auth_ws(email=email, password="pw", nickname="ws_init")

    gameplay_id = await create_game(
        client, rows=5, columns=5, mine_count=2, session=session
    )

    with ws_client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
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


@pytest.mark.asyncio
async def test_websocket_game_over_loss_schema(client, auth_ws, ws_client, session):
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-loss-{uuid.uuid4().hex[:8]}@example.com"
    auth_ws(email=email, password="pw", nickname="ws_loss")

    gameplay_id = await create_game(
        client, rows=3, columns=3, mine_count=7, session=session
    )

    game_over = None
    finished = False
    with ws_client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
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


@pytest.mark.asyncio
async def test_websocket_get_game_state_returns_current_state(
    client, auth_ws, ws_client, session
):
    email = f"ws-getstate-{uuid.uuid4().hex[:8]}@example.com"
    auth_ws(email=email, password="pw", nickname="ws_getstate")

    gameplay_id = await create_game(
        client, rows=5, columns=5, mine_count=5, session=session
    )

    with ws_client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
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


@pytest.mark.asyncio
async def test_websocket_board_state_shows_revealed_cell(
    client, auth_ws, ws_client, session
):
    from starlette.websockets import WebSocketDisconnect

    email = f"ws-verify-{uuid.uuid4().hex[:8]}@example.com"
    auth_ws(email=email, password="pw", nickname="ws_verify")

    gameplay_id = await create_game(
        client, rows=5, columns=5, mine_count=3, session=session
    )

    try:
        with ws_client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
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
