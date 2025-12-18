import uuid

import pytest

from backend.schemas.user import FriendRequestResponse


@pytest.mark.asyncio
async def test_get_pending_requests_returns_paginated_response(authenticated_clients):
    client = authenticated_clients[0]

    resp = await client.http.get("/api/friend-requests/pending")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"sender-{uuid.uuid4().hex[:8]}@example.com",
                "password": "senderpw",
                "nickname": "sender",
            },
            {
                "email": f"receiver-{uuid.uuid4().hex[:8]}@example.com",
                "password": "receiverpw",
                "nickname": "receiver",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_get_pending_requests_shows_incoming_request(authenticated_clients):
    client1, client2 = authenticated_clients

    user2_resp = await client2.http.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    await client1.http.post("/api/friend-requests", json={"friend_id": user2_id})
    pending_resp = await client2.http.get("/api/friend-requests/pending")
    assert pending_resp.status_code == 200
    data = pending_resp.json()

    assert data["total"] >= 1
    for item in data["items"]:
        fr = FriendRequestResponse(**item)
        assert fr.id is not None
        assert fr.ws_type == "friend_request"
        assert fr.user is not None
        assert fr.friend is not None
        assert fr.status.value in ["pending", "accepted", "rejected"]


@pytest.mark.asyncio
async def test_get_pending_requests_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.get("/api/friend-requests/pending")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_sent_requests_returns_paginated_response(authenticated_clients):
    client = authenticated_clients[0]

    resp = await client.http.get("/api/friend-requests/sent")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"outsender-{uuid.uuid4().hex[:8]}@example.com",
                "password": "outsenderpw",
                "nickname": "outsender",
            },
            {
                "email": f"outreceiver-{uuid.uuid4().hex[:8]}@example.com",
                "password": "outreceiverpw",
                "nickname": "outreceiver",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_get_sent_requests_shows_outgoing_request(authenticated_clients):
    client1, client2 = authenticated_clients

    user2_resp = await client2.http.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    await client1.http.post("/api/friend-requests", json={"friend_id": user2_id})

    sent_resp = await client1.http.get("/api/friend-requests/sent")
    assert sent_resp.status_code == 200
    data = sent_resp.json()

    assert data["total"] >= 1
    friend_ids = [item["friend"]["id"] for item in data["items"]]
    assert user2_id in friend_ids


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"reqsender-{uuid.uuid4().hex[:8]}@example.com",
                "password": "reqsenderpw",
                "nickname": "reqsender",
            },
            {
                "email": f"reqreceiver-{uuid.uuid4().hex[:8]}@example.com",
                "password": "reqreceiverpw",
                "nickname": "reqreceiver",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_send_friend_request_returns_friend_request_response(
    authenticated_clients,
):
    client1, client2 = authenticated_clients

    user2_resp = await client2.http.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    resp = await client1.http.post("/api/friend-requests", json={"friend_id": user2_id})

    assert resp.status_code == 200
    data = resp.json()

    fr = FriendRequestResponse(**data)
    assert fr.id is not None
    assert fr.ws_type == "friend_request"
    assert fr.user is not None
    assert fr.friend is not None
    assert str(fr.friend.id) == user2_id
    assert fr.status.value == "pending"

    assert fr.user.nickname == "reqsender"
    assert fr.friend.nickname == "reqreceiver"


@pytest.mark.asyncio
async def test_send_friend_request_to_self_returns_400(authenticated_clients):
    client = authenticated_clients[0]

    me_resp = await client.http.get("/api/auth/me")
    my_id = me_resp.json()["id"]

    resp = await client.http.post("/api/friend-requests", json={"friend_id": my_id})

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"dupreq1-{uuid.uuid4().hex[:8]}@example.com",
                "password": "dupreq1pw",
                "nickname": "dupreq1",
            },
            {
                "email": f"dupreq2-{uuid.uuid4().hex[:8]}@example.com",
                "password": "dupreq2pw",
                "nickname": "dupreq2",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_send_friend_request_duplicate_returns_400(authenticated_clients):
    client1, client2 = authenticated_clients

    user2_resp = await client2.http.get("/api/auth/me")
    user2_id = user2_resp.json()["id"]

    resp1 = await client1.http.post(
        "/api/friend-requests", json={"friend_id": user2_id}
    )
    assert resp1.status_code == 200

    resp2 = await client1.http.post(
        "/api/friend-requests", json={"friend_id": user2_id}
    )
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_send_friend_request_to_nonexistent_user_returns_404(
    authenticated_clients,
):
    client = authenticated_clients[0]

    fake_id = str(uuid.uuid4())
    resp = await client.http.post("/api/friend-requests", json={"friend_id": fake_id})

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_friend_request_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post(
        "/api/friend-requests", json={"friend_id": str(uuid.uuid4())}
    )
    assert resp.status_code == 401
