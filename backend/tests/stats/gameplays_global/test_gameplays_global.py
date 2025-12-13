import uuid

import pytest


@pytest.mark.anyio
async def test_get_gameplays_global_ranking_returns_paginated_response(client):
    resp = await client.get(
        "/api/stats/gameplays/global",
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


@pytest.mark.anyio
async def test_get_gameplays_global_ranking_validates_schema(client, auth):

    email = f"globalrank-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="globalrankpw", nickname="globalrankuser")

    resp = await client.get(
        "/api/stats/gameplays/global",
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


@pytest.mark.anyio
async def test_get_gameplays_global_ranking_missing_params_returns_422(client):
    resp = await client.get("/api/stats/gameplays/global")
    assert resp.status_code == 422
