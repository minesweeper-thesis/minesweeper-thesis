import pytest
from httpx_ws import WebSocketDisconnect

from backend.tests.singleplayer.helpers import create_game


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_initial_game_state_schema(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(bundle.http, rows=5, columns=5, mine_count=2)

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        data = await ws.receive_json()

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


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_game_over_loss_schema(authenticated_clients, session):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(bundle.http, rows=3, columns=3, mine_count=7)

    game_over = None
    finished = False
    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        initial = await ws.receive_json()
        start_field = initial["start_field"]

        for x in range(3):
            if finished:
                break
            for y in range(3):
                if finished:
                    break
                if (x, y) == tuple(start_field):
                    continue
                await ws.send_json({"type": "reveal_one", "cell": (x, y)})
                try:
                    data = await ws.receive_json()
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


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_get_game_state_returns_current_state(
    authenticated_clients, session
):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(bundle.http, rows=5, columns=5, mine_count=5)

    async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
        initial = await ws.receive_json()
        start_field = initial["start_field"]

        await ws.send_json({"type": "reveal_one", "cell": start_field})
        await ws.receive_json()

        await ws.send_json({"type": "get_state"})
        data = await ws.receive_json()

        assert data["type"] == "game_state"
        assert data["status"] == "in_progress"
        assert "board" in data
        assert data["board"] is not None
        assert isinstance(data["board"], list)
        assert len(data["board"]) == 5
        for row in data["board"]:
            assert len(row) == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_websocket_board_state_shows_revealed_cell(
    authenticated_clients, session
):
    bundle = authenticated_clients[0]

    gameplay_id = await create_game(bundle.http, rows=5, columns=5, mine_count=3)

    try:
        async with bundle.ws(f"/game/single/{gameplay_id}") as ws:
            initial = await ws.receive_json()
            start_field = initial["start_field"]

            await ws.send_json({"type": "reveal_one", "cell": start_field})
            reveal_data = await ws.receive_json()

            if reveal_data["type"] == "reveal":
                await ws.send_json({"type": "get_state"})
                state_data = await ws.receive_json()
                board = state_data["board"]

                cell_value = board[start_field[0]][start_field[1]]

                assert cell_value != -3, f"Cell should be revealed, got {cell_value}"
            elif reveal_data["type"] == "game_over":
                pass
    except WebSocketDisconnect:
        pass
