import uuid

import pytest


@pytest.mark.asyncio
async def test_get_users_friends_ranking_requires_auth(client):
    resp = await client.get(
        "/api/stats/users/friends",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
            "compare_by": "win_rate",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_users_friends_ranking_returns_paginated_response(client, auth):
    email = f"userfriendsrank-{uuid.uuid4().hex[:8]}@example.com"
    await auth(
        email=email, password="userfriendsrankpw", nickname="userfriendsrankuser"
    )

    resp = await client.get(
        "/api/stats/users/friends",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
            "compare_by": "win_rate",
        },
    )

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_users_friends_ranking_by_average_time(client, auth):
    email = f"friendsavgtime-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="friendsavgtimepw", nickname="friendsavgtimeuser")

    resp = await client.get(
        "/api/stats/users/friends",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
            "compare_by": "average_time",
        },
    )

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
