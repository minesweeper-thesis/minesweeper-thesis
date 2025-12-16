import uuid

import pytest


@pytest.mark.asyncio
async def test_create_lobby_returns_lobby_response(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.post("/api/lobbies")

    assert resp.status_code == 200
    data = resp.json()

    assert "id" in data
    assert "host" in data
    assert "users" in data
    assert "game_config" in data

    uuid.UUID(str(data["id"]))
    assert isinstance(data["users"], list)

    host = data["host"]
    assert "id" in host
    assert "nickname" in host
    assert host["nickname"] == "test"

    config = data["game_config"]
    assert "rounds" in config
    assert "max_round_time" in config
    assert "difficulty_level" in config
    assert "game_mode" in config
    assert "generator" in config

    dl = config["difficulty_level"]
    assert "rows" in dl
    assert "columns" in dl
    assert "mine_count" in dl


@pytest.mark.asyncio
async def test_create_lobby_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post("/api/lobbies")
    assert resp.status_code == 401
