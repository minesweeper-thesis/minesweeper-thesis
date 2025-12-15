import uuid

import pytest

from backend.schemas.user import UserResponse


@pytest.mark.asyncio
async def test_search_users_returns_paginated_user_response(client, auth):
    email = f"searchable-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="searchpw", nickname="searchableuser")

    resp = await client.get("/api/search", params={"query": "searchable"})

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

        uuid.UUID(str(user.id))


@pytest.mark.asyncio
async def test_search_users_finds_matching_user(client, auth):
    unique_name = f"unique{uuid.uuid4().hex[:8]}"
    email = f"{unique_name}@example.com"
    await auth(email=email, password="findpw", nickname=unique_name)

    resp = await client.get("/api/search", params={"query": unique_name[:10]})

    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] >= 1
    nicknames = [item["nickname"] for item in data["items"]]
    assert unique_name in nicknames


@pytest.mark.asyncio
async def test_search_users_empty_query_works(client, auth):
    email = f"emptysearch-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="emptypw", nickname="emptyquery")

    resp = await client.get("/api/search", params={"query": ""})
    assert resp.status_code in [200, 422]


@pytest.mark.asyncio
async def test_search_users_no_auth_works(client):
    resp = await client.get("/api/search", params={"query": "test"})

    assert resp.status_code in [200, 401]
