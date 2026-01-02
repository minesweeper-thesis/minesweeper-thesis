import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_get_users_global_ranking_by_win_rate(client_no_auth):
    resp = await client_no_auth.get(
        "/stats/users/global",
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


@pytest.mark.asyncio(loop_scope="session")
async def test_get_users_global_ranking_by_average_time(client_no_auth):
    resp = await client_no_auth.get(
        "/stats/users/global",
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


@pytest.mark.asyncio(loop_scope="session")
async def test_get_users_global_ranking_validates_schema(client_no_auth):
    resp = await client_no_auth.get(
        "/stats/users/global",
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

        assert "user" in item
        assert "win_rate" in item
        assert "average_time" in item
        assert "total_games" in item
        assert "won_games" in item

        assert isinstance(item["win_rate"], (int, float))
        assert isinstance(item["average_time"], (int, float))
        assert isinstance(item["total_games"], int)
        assert isinstance(item["won_games"], int)

        user = item["user"]
        assert "id" in user
        assert "nickname" in user


@pytest.mark.asyncio(loop_scope="session")
async def test_get_users_global_ranking_invalid_compare_by_returns_422(client_no_auth):
    resp = await client_no_auth.get(
        "/stats/users/global",
        params={
            "rows": 10,
            "cols": 10,
            "mine_count": 15,
            "compare_by": "invalid_value",
        },
    )
    assert resp.status_code == 422
