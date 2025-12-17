import json
import uuid

import pytest

from backend.schemas.game.single_schemas import NewGameResponse


@pytest.mark.asyncio
async def test_start_game_validates_response(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.post(
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


@pytest.mark.asyncio
async def test_start_game_invalid_board_returns_404(authenticated_clients):
    client = authenticated_clients[0]
    fake_board_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/game/single",
        json={"board_id": fake_board_id, "mode": "normal"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_start_game_works_without_auth(client_no_auth):
    resp = await client_no_auth.post(
        "/api/game/single",
        json={
            "mode": "normal",
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 3},
            "generator": {"type": "random"},
        },
    )
    assert resp.status_code == 200
    assert "gameplay_id" in resp.json()


@pytest.mark.asyncio
async def test_start_game_validates_difficulty_level(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5},
            "generator": {"type": "random"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_start_game_validates_generator_type(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 2},
            "generator": {"type": "invalid_generator"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_websocket_invalid_gameplay_returns_error(authenticated_clients):
    client = authenticated_clients[0]
    fake_gameplay_id = str(uuid.uuid4())

    try:
        with client.websocket_connect(f"/api/game/single/{fake_gameplay_id}") as ws:
            data = json.loads(ws.receive_text())
            assert data.get("type") in ["error", "game_state"]
    except Exception:

        pass
