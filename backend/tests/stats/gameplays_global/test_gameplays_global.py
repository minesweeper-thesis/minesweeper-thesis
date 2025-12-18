import uuid

import pytest


@pytest.mark.asyncio
async def test_get_gameplays_global_ranking_returns_paginated_response(client_no_auth):
    resp = await client_no_auth.get(
        "/stats/gameplays/global",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
        },
    )

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_gameplays_global_ranking_validates_schema(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.http.get(
        "/stats/gameplays/global",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
        },
    )

    assert resp.status_code == 200
    data = resp.json()

    for item in data["items"]:

        assert "gameplay_id" in item
        assert "user" in item
        assert "time" in item

        uuid.UUID(str(item["gameplay_id"]))
        assert isinstance(item["time"], (int, float))

        user = item["user"]
        assert "id" in user
        assert "nickname" in user
        assert "email" in user


@pytest.mark.asyncio
async def test_get_gameplays_global_ranking_missing_params_returns_422(client_no_auth):
    resp = await client_no_auth.get("/stats/gameplays/global")
    assert resp.status_code == 422
