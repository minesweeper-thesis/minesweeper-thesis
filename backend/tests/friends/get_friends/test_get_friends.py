import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.schemas.user import UserResponse


@pytest.mark.asyncio
async def test_get_friends_returns_paginated_user_response(authenticated_clients):
    client = authenticated_clients[0]

    resp = await client.get("/api/friends")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_friends_without_auth_returns_401():
    async_client = AsyncClient(
        transport=ASGITransport(app), base_url="https://testserver"
    )
    resp = await async_client.get("/api/friends")
    assert resp.status_code == 401
    await async_client.aclose()


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"user1-{uuid.uuid4().hex[:8]}@example.com",
                "password": "user1pw",
                "nickname": "user1friend",
            },
            {
                "email": f"user2-{uuid.uuid4().hex[:8]}@example.com",
                "password": "user2pw",
                "nickname": "user2friend",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_get_friends_shows_accepted_friend(authenticated_clients):
    client1, client2 = authenticated_clients

    user2_resp = await client2.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    req_resp = await client1.post("/api/friend-requests", json={"friend_id": user2_id})

    assert req_resp.status_code == 200
    friend_request_id = req_resp.json()["id"]

    accept_resp = await client2.post(f"/api/friend-requests/{friend_request_id}/accept")

    assert accept_resp.status_code in [200, 204]
    friends_resp = await client1.get("/api/friends")
    assert friends_resp.status_code == 200
    data = friends_resp.json()

    assert data["total"] >= 1
    for item in data["items"]:
        user = UserResponse(**item)
        assert user.id == uuid.UUID(user2_id)
        assert user.nickname == "user2friend"
