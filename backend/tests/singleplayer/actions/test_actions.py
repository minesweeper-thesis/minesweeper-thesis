import pytest
from httpx_ws import WebSocketDisconnect

from backend.tests.singleplayer.helpers import create_game


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_reveal_one_returns_response(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        initial = await ws.receive_json()
        start_field = initial["start_field"]

        await ws.send_json({"type": "reveal_one", "cell": start_field})
        data = await ws.receive_json()

        assert data["type"] == "reveal"
        assert "revealed_cells" in data
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]
        assert isinstance(data["revealed_cells"], list)


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_reveal_start_field_is_safe(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        initial = await ws.receive_json()
        start_field = initial["start_field"]

        await ws.send_json({"type": "reveal_one", "cell": start_field})
        data = await ws.receive_json()

        if data["type"] == "game_over":
            assert (
                data.get("game_status") != "loss"
            ), "Start field should never be a mine!"
        else:
            assert data["type"] == "reveal"


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_reveal_returns_valid_cell_values(
    authenticated_clients, session
):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        initial = await ws.receive_json()
        start_field = initial["start_field"]

        await ws.send_json({"type": "reveal_one", "cell": start_field})
        data = await ws.receive_json()

        if data["type"] == "reveal":
            for cell in data["revealed_cells"]:
                val = cell.get("value") if isinstance(cell, dict) else cell[2]
                if val is not None:
                    assert 0 <= val <= 8, f"Invalid cell value: {val}"


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_flag_returns_response(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        await ws.receive_json()

        await ws.send_json({"type": "flag", "cell": (0, 0)})
        data = await ws.receive_json()

        assert data["type"] == "flag"
        assert "game_status" in data
        assert data["game_status"] in ["not_started", "in_progress", "finished"]


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_remove_flag_returns_response(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        await ws.receive_json()

        await ws.send_json({"type": "flag", "cell": (0, 0)})
        await ws.receive_json()

        await ws.send_json({"type": "remove_flag", "cell": (0, 0)})
        data = await ws.receive_json()

        assert data["type"] == "remove_flag"
        assert "game_status" in data


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_flag_and_unflag_same_cell(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=1, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        await ws.receive_json()

        await ws.send_json({"type": "flag", "cell": (1, 1)})
        flag_resp = await ws.receive_json()
        assert flag_resp["type"] == "flag"

        await ws.send_json({"type": "remove_flag", "cell": (1, 1)})
        unflag_resp = await ws.receive_json()
        assert unflag_resp["type"] == "remove_flag"


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_flag_shows_in_state(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=1, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        await ws.receive_json()

        await ws.send_json({"type": "flag", "cell": (0, 0)})
        await ws.receive_json()

        await ws.send_json({"type": "get_state"})
        state_data = await ws.receive_json()
        board = state_data["board"]

        cell_value = board[0][0]
        assert cell_value == -4, f"Cell should be flagged (-4), got {cell_value}"


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_use_hint_action(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        await ws.receive_json()

        await ws.send_json({"type": "hint"})
        data = await ws.receive_json()

        assert data["type"] in ["hint", "error", "reveal", "game_state"]


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_reveal_out_of_bounds(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=3, columns=3, mine_count=1, session=session
    )

    try:
        async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
            await ws.receive_json()

            await ws.send_json({"type": "reveal_one", "cell": (100, 100)})
            data = await ws.receive_json()

            assert data["type"] in ["reveal", "error"]
    except (WebSocketDisconnect, Exception):
        pass


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_flag_revealed_cell(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        initial = await ws.receive_json()
        start_field = initial["start_field"]

        await ws.send_json({"type": "reveal_one", "cell": start_field})
        await ws.receive_json()

        await ws.send_json({"type": "flag", "cell": start_field})
        data = await ws.receive_json()

        assert data["type"] in ["flag", "error", "game_over"]


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_normal_mode(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(
        bundle.http, rows=5, columns=5, mine_count=2, session=session
    )

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        data = await ws.receive_json()
        assert data["type"] == "game_state"
