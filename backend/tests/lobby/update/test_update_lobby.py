import uuid

import pytest


@pytest.mark.asyncio
async def test_update_lobby_config_success(client, auth):
    email = f"updatelobby-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="updatelobbypw", nickname="updatelobbyhost")

    create_resp = await client.post("/api/lobbies")
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

    resp = await client.put(f"/api/lobbies/{lobby_id}", json=new_config)
    assert resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_update_lobby_config_without_auth_returns_401(client):
    resp = await client.put(
        f"/api/lobbies/{uuid.uuid4()}",
        json={
            "rounds": 3,
            "max_round_time": 120,
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 5},
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert resp.status_code == 401
