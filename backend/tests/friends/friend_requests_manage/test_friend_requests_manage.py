import uuid

import pytest


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"acceptsender-{uuid.uuid4().hex[:8]}@example.com",
                "password": "acceptsenderpw",
                "nickname": "acceptsender",
            },
            {
                "email": f"acceptreceiver-{uuid.uuid4().hex[:8]}@example.com",
                "password": "acceptreceiverpw",
                "nickname": "acceptreceiver",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_accept_friend_request_success(authenticated_clients):
    client1, client2 = authenticated_clients

    user2_resp = await client2.http.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    req_resp = await client1.http.post(
        "/api/friend-requests", json={"friend_id": user2_id}
    )

    assert req_resp.status_code == 200
    friend_request_id = req_resp.json()["id"]

    accept_resp = await client2.http.post(
        f"/api/friend-requests/{friend_request_id}/accept"
    )
    assert accept_resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_accept_nonexistent_request_returns_404(authenticated_clients):
    client = authenticated_clients[0]

    fake_id = str(uuid.uuid4())
    resp = await client.http.post(f"/api/friend-requests/{fake_id}/accept")

    assert resp.status_code == 404


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"rejectsender-{uuid.uuid4().hex[:8]}@example.com",
                "password": "rejectsenderpw",
                "nickname": "rejectsender",
            },
            {
                "email": f"rejectreceiver-{uuid.uuid4().hex[:8]}@example.com",
                "password": "rejectreceiverpw",
                "nickname": "rejectreceiver",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_reject_friend_request_success(authenticated_clients):
    client1, client2 = authenticated_clients

    user2_resp = await client2.http.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    req_resp = await client1.http.post(
        "/api/friend-requests", json={"friend_id": user2_id}
    )

    assert req_resp.status_code == 200
    friend_request_id = req_resp.json()["id"]

    reject_resp = await client2.http.post(
        f"/api/friend-requests/{friend_request_id}/reject"
    )
    assert reject_resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_reject_nonexistent_request_returns_404(authenticated_clients):
    client = authenticated_clients[0]

    fake_id = str(uuid.uuid4())
    resp = await client.http.post(f"/api/friend-requests/{fake_id}/reject")

    assert resp.status_code == 404
