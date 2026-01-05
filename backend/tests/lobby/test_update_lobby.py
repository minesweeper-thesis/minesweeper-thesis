import uuid

import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_update_lobby_config_success(authenticated_clients):
    client = authenticated_clients[0]
    create_resp = await client.http.post("/lobbies")
    lobby_id = create_resp.json()["id"]

    new_config = {
        "rounds": 5,
        "max_round_time": 180,
        "difficulty_level": {
            "rows": 10,
            "columns": 10,
            "mine_count": 15,
        },
        "game_mode": "hardcore",
        "generator": {
            "type": "random",
            "settings": None,
        },
    }

    resp = await client.http.put(f"/lobbies/{lobby_id}", json=new_config)
    assert resp.status_code in [200, 204]


@pytest.mark.asyncio(loop_scope="session")
async def test_update_lobby_config_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.put(
        f"/lobbies/{uuid.uuid4()}",
        json={
            "rounds": 3,
            "max_round_time": 120,
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 5},
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert resp.status_code == 401
