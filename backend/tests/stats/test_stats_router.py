"""
Comprehensive stats router tests.
Tests: GET /stats/gameplays/global, GET /stats/gameplays/friends,
       GET /stats/users/global, GET /stats/users/friends
"""

import uuid

# =============================================================================
# GET /stats/gameplays/global Tests
# =============================================================================


def test_get_gameplays_global_ranking_returns_paginated_response(client):
    """GET /stats/gameplays/global returns Page[GameplayRankingResponse]."""
    resp = client.get(
        "/api/stats/gameplays/global",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
        },
    )

    assert resp.status_code == 200
    data = resp.json()

    # Validate pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)


def test_get_gameplays_global_ranking_validates_schema(client, auth):
    """GET /stats/gameplays/global items follow GameplayRankingResponse schema."""
    # First create a gameplay to have data
    email = f"globalrank-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="globalrankpw", nickname="globalrankuser")

    resp = client.get(
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
        # Validate GameplayRankingResponse schema
        assert "gameplay_id" in item
        assert "user" in item
        assert "time" in item

        # Validate types
        uuid.UUID(str(item["gameplay_id"]))
        assert isinstance(item["time"], (int, float))

        # Validate user UserResponse
        user = item["user"]
        assert "id" in user
        assert "nickname" in user
        assert "email" in user


def test_get_gameplays_global_ranking_missing_params_returns_422(client):
    """GET /stats/gameplays/global without required params returns 422."""
    resp = client.get("/api/stats/gameplays/global")
    assert resp.status_code == 422


# =============================================================================
# GET /stats/gameplays/friends Tests
# =============================================================================


def test_get_gameplays_friends_ranking_requires_auth(client):
    """GET /stats/gameplays/friends without auth returns 401."""
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
    """GET /stats/gameplays/friends returns Page[GameplayRankingResponse]."""
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


# =============================================================================
# GET /stats/users/global Tests
# =============================================================================


def test_get_users_global_ranking_by_win_rate(client):
    """GET /stats/users/global with compare_by=win_rate."""
    resp = client.get(
        "/api/stats/users/global",
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


def test_get_users_global_ranking_by_average_time(client):
    """GET /stats/users/global with compare_by=average_time."""
    resp = client.get(
        "/api/stats/users/global",
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


def test_get_users_global_ranking_validates_schema(client):
    """GET /stats/users/global items follow UserRankingResponse schema."""
    resp = client.get(
        "/api/stats/users/global",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
            "compare_by": "win_rate",
        },
    )

    assert resp.status_code == 200
    data = resp.json()

    for item in data["items"]:
        # Validate UserRankingResponse schema
        assert "user" in item
        assert "win_rate" in item
        assert "average_time" in item
        assert "total_games" in item
        assert "won_games" in item

        # Validate types
        assert isinstance(item["win_rate"], (int, float))
        assert isinstance(item["average_time"], (int, float))
        assert isinstance(item["total_games"], int)
        assert isinstance(item["won_games"], int)

        # Validate user UserResponse
        user = item["user"]
        assert "id" in user
        assert "nickname" in user


def test_get_users_global_ranking_invalid_compare_by_returns_422(client):
    """GET /stats/users/global with invalid compare_by returns 422."""
    resp = client.get(
        "/api/stats/users/global",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
            "compare_by": "invalid_value",
        },
    )
    assert resp.status_code == 422


# =============================================================================
# GET /stats/users/friends Tests
# =============================================================================


def test_get_users_friends_ranking_requires_auth(client):
    """GET /stats/users/friends without auth returns 401."""
    resp = client.get(
        "/api/stats/users/friends",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
            "compare_by": "win_rate",
        },
    )
    assert resp.status_code == 401


def test_get_users_friends_ranking_returns_paginated_response(client, auth):
    """GET /stats/users/friends returns Page[UserRankingResponse]."""
    email = f"userfriendsrank-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="userfriendsrankpw", nickname="userfriendsrankuser")

    resp = client.get(
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


def test_get_users_friends_ranking_by_average_time(client, auth):
    """GET /stats/users/friends with compare_by=average_time."""
    email = f"friendsavgtime-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="friendsavgtimepw", nickname="friendsavgtimeuser")

    resp = client.get(
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
