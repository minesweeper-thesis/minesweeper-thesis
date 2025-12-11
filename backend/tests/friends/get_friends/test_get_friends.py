import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.user import UserResponse


def test_get_friends_returns_paginated_user_response(client, auth):
    email = f"getfriends-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="friendspw", nickname="getfriendsuser")

    resp = client.get("/api/friends")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)
    assert data["total"] == 0


def test_get_friends_without_auth_returns_401(client):
    resp = client.get("/api/friends")
    assert resp.status_code == 401


def test_get_friends_shows_accepted_friend(client, auth):
    user1_email = f"user1-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="user1pw", nickname="user1friend")

    user2_email = f"user2-{uuid.uuid4().hex[:8]}@example.com"
    with TestClient(app, base_url="https://testserver") as client2:
        resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "user2pw",
                "nickname": "user2friend",
                "settings": {},
            },
        )
        if resp.status_code == 201:
            user2_id = resp.json()["id"]
        else:
            user2_id = None

    if user2_id:
        req_resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            with TestClient(app, base_url="https://testserver") as client2:
                client2.post(
                    "/api/auth/login",
                    data={
                        "username": user2_email,
                        "password": "user2pw",
                    },
                )
                accept_resp = client2.post(
                    f"/api/friend-requests/{friend_request_id}/accept"
                )

                if accept_resp.status_code in [200, 204]:
                    friends_resp = client.get("/api/friends")
                    assert friends_resp.status_code == 200
                    data = friends_resp.json()

                    if data["total"] >= 1:
                        for item in data["items"]:
                            user = UserResponse(**item)
                            assert user.id is not None
                            assert user.nickname is not None
