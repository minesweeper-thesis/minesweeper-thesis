import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.anyio
async def test_delete_friend_removes_friendship(client, auth):

    user1_email = f"delfriend1-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=user1_email, password="delfriend1pw", nickname="delfriend1")

    user2_email = f"delfriend2-{uuid.uuid4().hex[:8]}@example.com"
    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://testserver"
    ) as client2:
        resp = await client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "delfriend2pw",
                "nickname": "delfriend2",
                "settings": {},
            },
        )
        user2_id = resp.json()["id"] if resp.status_code == 201 else None

    if user2_id:

        req_resp = await client.post(
            "/api/friend-requests", json={"friend_id": user2_id}
        )
        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            async with AsyncClient(
                transport=ASGITransport(app), base_url="https://testserver"
            ) as client2:
                await client2.post(
                    "/api/auth/login",
                    data={
                        "username": user2_email,
                        "password": "delfriend2pw",
                    },
                )
                await client2.post(f"/api/friend-requests/{friend_request_id}/accept")

            del_resp = await client.delete(f"/api/friends/{user2_id}")
            assert del_resp.status_code in [200, 204]

            friends_resp = await client.get("/api/friends")
            data = friends_resp.json()
            friend_ids = [item["id"] for item in data["items"]]
            assert user2_id not in friend_ids


@pytest.mark.anyio
async def test_delete_non_friend_returns_400(client, auth):
    email = f"delnonfriend-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="delnonfriendpw", nickname="delnonfriend")

    fake_friend_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/friends/{fake_friend_id}")

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_delete_friend_without_auth_returns_401(client):
    resp = await client.delete(f"/api/friends/{uuid.uuid4()}")
    assert resp.status_code == 401
