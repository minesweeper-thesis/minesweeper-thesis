
import uuid

def test_get_gameplays_friends_ranking_requires_auth(client):
    resp = client.get(
        "/api/stats/gameplays/friends",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
        },
    )
    assert resp.status_code == 401

def test_get_gameplays_friends_ranking_returns_paginated_response(client, auth):
    email = f"friendsrank-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="friendsrankpw", nickname="friendsrankuser")

    resp = client.get(
        "/api/stats/gameplays/friends",
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
    assert isinstance(data["items"], list)
