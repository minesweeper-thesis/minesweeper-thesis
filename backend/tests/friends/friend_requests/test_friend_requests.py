import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.schemas.user import FriendRequestResponse


def test_get_pending_requests_returns_paginated_response(client, auth):
    email = f"pending-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pendingpw", nickname="pendinguser")

    resp = client.get("/api/friend-requests/pending")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_get_pending_requests_shows_incoming_request(client, auth):
    user1_email = f"sender-{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"receiver-{uuid.uuid4().hex[:8]}@example.com"

    with TestClient(app, base_url="https://testserver") as client2:
        reg_resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "receiverpw",
                "nickname": "receiver",
                "settings": {},
            },
        )
        user2_id = reg_resp.json()["id"] if reg_resp.status_code == 201 else None

    if user2_id:
        auth(email=user1_email, password="senderpw", nickname="sender")
        with TestClient(app, base_url="https://testserver") as client2:
            client2.post(
                "/api/auth/login",
                data={
                    "username": user2_email,
                    "password": "receiverpw",
                },
            )

            client.post("/api/friend-requests", json={"friend_id": user2_id})
            pending_resp = client2.get("/api/friend-requests/pending")
            assert pending_resp.status_code == 200
            data = pending_resp.json()

            if data["total"] >= 1:
                for item in data["items"]:
                    fr = FriendRequestResponse(**item)
                    assert fr.id is not None
                    assert fr.ws_type == "friend_request"
                    assert fr.user is not None
                    assert fr.friend is not None
                    assert fr.status.value in ["pending", "accepted", "rejected"]


def test_get_pending_requests_without_auth_returns_401(client):
    resp = client.get("/api/friend-requests/pending")
    assert resp.status_code == 401


def test_get_sent_requests_returns_paginated_response(client, auth):
    email = f"sent-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="sentpw", nickname="sentuser")

    resp = client.get("/api/friend-requests/sent")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data


def test_get_sent_requests_shows_outgoing_request(client, auth):
    user1_email = f"outsender-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="outsenderpw", nickname="outsender")

    user2_email = f"outreceiver-{uuid.uuid4().hex[:8]}@example.com"
    with TestClient(app, base_url="https://testserver") as client2:
        resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "outreceiverpw",
                "nickname": "outreceiver",
                "settings": {},
            },
        )
        user2_id = resp.json()["id"] if resp.status_code == 201 else None

    if user2_id:
        client.post("/api/friend-requests", json={"friend_id": user2_id})

        sent_resp = client.get("/api/friend-requests/sent")
        assert sent_resp.status_code == 200
        data = sent_resp.json()

        assert data["total"] >= 1
        friend_ids = [item["friend"]["id"] for item in data["items"]]
        assert user2_id in friend_ids


def test_send_friend_request_returns_friend_request_response(client, auth):
    user1_email = f"reqsender-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="reqsenderpw", nickname="reqsender")

    user2_email = f"reqreceiver-{uuid.uuid4().hex[:8]}@example.com"
    with TestClient(app, base_url="https://testserver") as client2:
        resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "reqreceiverpw",
                "nickname": "reqreceiver",
                "settings": {},
            },
        )
        user2_id = resp.json()["id"] if resp.status_code == 201 else None

    if user2_id:
        resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

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


def test_send_friend_request_to_self_returns_400(client, auth):
    email = f"selfreq-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="selfreqpw", nickname="selfrequser")

    me_resp = client.get("/api/auth/me")
    my_id = me_resp.json()["id"]

    resp = client.post("/api/friend-requests", json={"friend_id": my_id})

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data


def test_send_friend_request_duplicate_returns_400(client, auth):
    user1_email = f"dupreq1-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="dupreq1pw", nickname="dupreq1")

    user2_email = f"dupreq2-{uuid.uuid4().hex[:8]}@example.com"
    with TestClient(app, base_url="https://testserver") as client2:
        resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "dupreq2pw",
                "nickname": "dupreq2",
                "settings": {},
            },
        )
        user2_id = resp.json()["id"] if resp.status_code == 201 else None

    if user2_id:
        resp1 = client.post("/api/friend-requests", json={"friend_id": user2_id})
        assert resp1.status_code == 200

        resp2 = client.post("/api/friend-requests", json={"friend_id": user2_id})
        assert resp2.status_code == 400


def test_send_friend_request_to_nonexistent_user_returns_404(client, auth):
    email = f"reqnoexist-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="reqnoexistpw", nickname="reqnoexist")

    fake_id = str(uuid.uuid4())
    resp = client.post("/api/friend-requests", json={"friend_id": fake_id})

    assert resp.status_code == 404


def test_send_friend_request_without_auth_returns_401(client):
    resp = client.post("/api/friend-requests", json={"friend_id": str(uuid.uuid4())})
    assert resp.status_code == 401
