import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"delfriend1-{uuid.uuid4().hex[:8]}@example.com",
                "password": "delfriend1pw",
                "nickname": "delfriend1",
            },
            {
                "email": f"delfriend2-{uuid.uuid4().hex[:8]}@example.com",
                "password": "delfriend2pw",
                "nickname": "delfriend2",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_delete_friend_removes_friendship(authenticated_clients):
    client1, client2 = authenticated_clients

    user2_resp = await client2.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    req_resp = await client1.post("/api/friend-requests", json={"friend_id": user2_id})
    assert req_resp.status_code == 200
    friend_request_id = req_resp.json()["id"]

    await client2.post(f"/api/friend-requests/{friend_request_id}/accept")

    del_resp = await client1.delete(f"/api/friends/{user2_id}")
    assert del_resp.status_code in [200, 204]

    friends_resp = await client1.get("/api/friends")
    data = friends_resp.json()
    friend_ids = [item["id"] for item in data["items"]]
    assert user2_id not in friend_ids


@pytest.mark.asyncio
async def test_delete_non_friend_returns_400(authenticated_clients):
    client = authenticated_clients[0]

    fake_friend_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/friends/{fake_friend_id}")

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_delete_friend_without_auth_returns_401(client_no_auth: AsyncClient):
    resp = await client_no_auth.delete(f"/api/friends/{uuid.uuid4()}")
    assert resp.status_code == 401
