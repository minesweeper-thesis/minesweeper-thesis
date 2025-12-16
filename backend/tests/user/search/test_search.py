import pytest

from backend.schemas.user import UserResponse


@pytest.mark.asyncio
async def test_search_users_returns_paginated_user_response(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.get("/api/search", params={"query": "te"})

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["pages"], int)
    assert isinstance(data["size"], int)

    for item in data["items"]:
        user = UserResponse(**item)
        assert user.id is not None
        assert user.nickname is not None
        assert user.email is not None


@pytest.mark.asyncio
async def test_search_users_finds_matching_user(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.get("/api/search", params={"query": "te"})

    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] >= 1
    nicknames = [item["nickname"] for item in data["items"]]
    assert "test" in nicknames


@pytest.mark.asyncio
async def test_search_users_no_auth_returns_401(client):
    resp = await client.get("/api/search", params={"query": "test"})

    assert resp.status_code == 401
