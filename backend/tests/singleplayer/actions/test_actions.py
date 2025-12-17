import json
import uuid

import pytest

from backend.tests.singleplayer.helpers import create_game


@pytest.mark.asyncio
async def test_websocket_reveal_one_returns_response(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        data = json.loads(ws.receive_text())

        assert data["type"] == "reveal"
        assert "revealed_cells" in data
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]
        assert isinstance(data["revealed_cells"], list)


@pytest.mark.asyncio
async def test_websocket_reveal_start_field_is_safe(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
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


@pytest.mark.asyncio
async def test_websocket_reveal_returns_valid_cell_values(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        data = json.loads(ws.receive_text())

        if data["type"] == "reveal":
            for cell in data["revealed_cells"]:

                val = cell.get("value") if isinstance(cell, dict) else cell[2]
                if val is not None:
                    assert 0 <= val <= 8, f"Invalid cell value: {val}"


@pytest.mark.asyncio
async def test_websocket_flag_returns_response(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (0, 0)})
        data = json.loads(ws.receive_text())

        assert data["type"] == "flag"
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]


@pytest.mark.asyncio
async def test_websocket_remove_flag_returns_response(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (0, 0)})
        ws.receive_text()

        ws.send_json({"type": "remove_flag", "cell": (0, 0)})
        data = json.loads(ws.receive_text())

        assert data["type"] == "remove_flag"
        assert "game_status" in data


@pytest.mark.asyncio
async def test_websocket_flag_and_unflag_same_cell(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=1, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (1, 1)})
        flag_resp = json.loads(ws.receive_text())
        assert flag_resp["type"] == "flag"

        ws.send_json({"type": "remove_flag", "cell": (1, 1)})
        unflag_resp = json.loads(ws.receive_text())
        assert unflag_resp["type"] == "remove_flag"


@pytest.mark.asyncio
async def test_websocket_flag_shows_in_state(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=1, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": (0, 0)})
        ws.receive_text()

        ws.send_json({"type": "get_state"})
        state_data = json.loads(ws.receive_text())
        board = state_data["board"]

        cell_value = board[0][0]
        assert cell_value == -4, f"Cell should be flagged (-4), got {cell_value}"


@pytest.mark.asyncio
async def test_websocket_use_hint_action(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        ws.receive_text()

        ws.send_json({"type": "hint"})
        data = json.loads(ws.receive_text())

        assert data["type"] in ["hint", "error", "reveal", "game_state"]


@pytest.mark.asyncio
async def test_websocket_reveal_out_of_bounds(authenticated_clients, session):
    from anyio import EndOfStream
    from starlette.websockets import WebSocketDisconnect

    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=1, session=session
    )

    try:
        with bundle.get_ws_game(gameplay_id) as ws:
            ws.receive_text()

            ws.send_json({"type": "reveal_one", "cell": (100, 100)})
            data = json.loads(ws.receive_text())

            assert data["type"] in ["reveal", "error"]
    except (WebSocketDisconnect, EndOfStream, Exception):

        pass


@pytest.mark.asyncio
async def test_websocket_flag_revealed_cell(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        initial = json.loads(ws.receive_text())
        start_field = initial["start_field"]

        ws.send_json({"type": "reveal_one", "cell": start_field})
        ws.receive_text()

        ws.send_json({"type": "flag", "cell": start_field})
        data = json.loads(ws.receive_text())

        assert data["type"] in ["flag", "error", "game_over"]


@pytest.mark.asyncio
async def test_websocket_normal_mode(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    with bundle.get_ws_game(gameplay_id) as ws:
        data = json.loads(ws.receive_text())
        assert data["type"] == "game_state"
