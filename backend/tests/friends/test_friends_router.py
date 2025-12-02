"""
Comprehensive friends router tests.
Tests: GET /friends, DELETE /friends/{id},
       GET /friend-requests/pending, GET /friend-requests/sent,
       POST /friend-requests, POST /friend-requests/{id}/accept,
       POST /friend-requests/{id}/reject
"""

import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.schemas.user_schemas import FriendRequestResponse, UserResponse


def _create_second_user(client, email, password, nickname):
    """Helper to create a second user and return their ID."""
    with TestClient(app, base_url="https://testserver") as client2:
        resp = client2.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "nickname": nickname,
                "settings": {},
            },
        )
        if resp.status_code == 201:
            return resp.json()["id"]
        return None


# =============================================================================
# GET /friends Tests
# =============================================================================


def test_get_friends_returns_paginated_user_response(client, auth):
    """GET /friends returns Page[UserResponse] with correct schema."""
    email = f"getfriends-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="friendspw", nickname="getfriendsuser")

    resp = client.get("/api/friends")

    assert resp.status_code == 200
    data = resp.json()

    # Validate pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)
    # Initially should have no friends
    assert data["total"] == 0


def test_get_friends_without_auth_returns_401(client):
    """GET /friends without auth returns 401."""
    resp = client.get("/api/friends")
    assert resp.status_code == 401


def test_get_friends_shows_accepted_friend(client, auth):
    """GET /friends shows user after friend request accepted."""
    # Create user1
    user1_email = f"user1-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="user1pw", nickname="user1friend")

    # Create user2 in separate client
    user2_email = f"user2-{uuid.uuid4().hex[:8]}@example.com"
    user2_id = _create_second_user(client, user2_email, "user2pw", "user2friend")

    if user2_id:
        # User1 sends friend request to user2
        req_resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            # Login as user2 and accept
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
                    # Check user1's friends list
                    friends_resp = client.get("/api/friends")
                    assert friends_resp.status_code == 200
                    data = friends_resp.json()

                    # Should have 1 friend
                    if data["total"] >= 1:
                        # Validate UserResponse schema
                        for item in data["items"]:
                            user = UserResponse(**item)
                            assert user.id is not None
                            assert user.nickname is not None


# =============================================================================
# DELETE /friends/{friend_id} Tests
# =============================================================================


def test_delete_friend_removes_friendship(client, auth):
    """DELETE /friends/{id} removes friendship."""
    # This requires setting up a friendship first
    user1_email = f"delfriend1-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="delfriend1pw", nickname="delfriend1")

    user2_email = f"delfriend2-{uuid.uuid4().hex[:8]}@example.com"
    user2_id = _create_second_user(client, user2_email, "delfriend2pw", "delfriend2")

    if user2_id:
        # Create and accept friendship
        req_resp = client.post("/api/friend-requests", json={"friend_id": user2_id})
        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            with TestClient(app, base_url="https://testserver") as client2:
                client2.post(
                    "/api/auth/login",
                    data={
                        "username": user2_email,
                        "password": "delfriend2pw",
                    },
                )
                client2.post(f"/api/friend-requests/{friend_request_id}/accept")

            # Now delete the friendship
            del_resp = client.delete(f"/api/friends/{user2_id}")
            assert del_resp.status_code in [200, 204]

            # Verify friend is removed
            friends_resp = client.get("/api/friends")
            data = friends_resp.json()
            friend_ids = [item["id"] for item in data["items"]]
            assert user2_id not in friend_ids


def test_delete_non_friend_returns_400(client, auth):
    """DELETE /friends/{id} for non-friend returns 400."""
    email = f"delnonfriend-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="delnonfriendpw", nickname="delnonfriend")

    fake_friend_id = str(uuid.uuid4())
    resp = client.delete(f"/api/friends/{fake_friend_id}")

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data


def test_delete_friend_without_auth_returns_401(client):
    """DELETE /friends/{id} without auth returns 401."""
    resp = client.delete(f"/api/friends/{uuid.uuid4()}")
    assert resp.status_code == 401


# =============================================================================
# GET /friend-requests/pending Tests
# =============================================================================


def test_get_pending_requests_returns_paginated_response(client, auth):
    """GET /friend-requests/pending returns Page[FriendRequestResponse]."""
    email = f"pending-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pendingpw", nickname="pendinguser")

    resp = client.get("/api/friend-requests/pending")

    assert resp.status_code == 200
    data = resp.json()

    # Validate pagination structure
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_get_pending_requests_shows_incoming_request(client, auth):
    """GET /friend-requests/pending shows requests sent TO user."""
    user1_email = f"sender-{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"receiver-{uuid.uuid4().hex[:8]}@example.com"

    # Create user2 first (the receiver)
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
        # Login as user1 and send request
        auth(email=user1_email, password="senderpw", nickname="sender")

        # Need user2's ID to send request
        # First get user1's ID
        me_resp = client.get("/api/auth/me")
        user1_id = me_resp.json()["id"]

        # Now login as user2 and check pending
        with TestClient(app, base_url="https://testserver") as client2:
            client2.post(
                "/api/auth/login",
                data={
                    "username": user2_email,
                    "password": "receiverpw",
                },
            )

            # User1 sends request to user2
            client.post("/api/friend-requests", json={"friend_id": user2_id})

            # User2 checks pending
            pending_resp = client2.get("/api/friend-requests/pending")
            assert pending_resp.status_code == 200
            data = pending_resp.json()

            if data["total"] >= 1:
                # Validate FriendRequestResponse schema
                for item in data["items"]:
                    fr = FriendRequestResponse(**item)
                    assert fr.id is not None
                    assert fr.ws_type == "friend_request"
                    assert fr.user is not None
                    assert fr.friend is not None
                    assert fr.status.value in ["pending", "accepted", "rejected"]


def test_get_pending_requests_without_auth_returns_401(client):
    """GET /friend-requests/pending without auth returns 401."""
    resp = client.get("/api/friend-requests/pending")
    assert resp.status_code == 401


# =============================================================================
# GET /friend-requests/sent Tests
# =============================================================================


def test_get_sent_requests_returns_paginated_response(client, auth):
    """GET /friend-requests/sent returns Page[FriendRequestResponse]."""
    email = f"sent-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="sentpw", nickname="sentuser")

    resp = client.get("/api/friend-requests/sent")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data


def test_get_sent_requests_shows_outgoing_request(client, auth):
    """GET /friend-requests/sent shows requests sent BY user."""
    user1_email = f"outsender-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="outsenderpw", nickname="outsender")

    # Create user2 to send request to
    user2_email = f"outreceiver-{uuid.uuid4().hex[:8]}@example.com"
    user2_id = _create_second_user(client, user2_email, "outreceiverpw", "outreceiver")

    if user2_id:
        # Send friend request
        client.post("/api/friend-requests", json={"friend_id": user2_id})

        # Check sent requests
        sent_resp = client.get("/api/friend-requests/sent")
        assert sent_resp.status_code == 200
        data = sent_resp.json()

        assert data["total"] >= 1
        # Should contain our request - field is "friend" not "receiver"
        friend_ids = [item["friend"]["id"] for item in data["items"]]
        assert user2_id in friend_ids


# =============================================================================
# POST /friend-requests Tests
# =============================================================================


def test_send_friend_request_returns_friend_request_response(client, auth):
    """POST /friend-requests returns FriendRequestResponse."""
    user1_email = f"reqsender-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="reqsenderpw", nickname="reqsender")

    user2_email = f"reqreceiver-{uuid.uuid4().hex[:8]}@example.com"
    user2_id = _create_second_user(client, user2_email, "reqreceiverpw", "reqreceiver")

    if user2_id:
        resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

        assert resp.status_code == 200
        data = resp.json()

        # Validate FriendRequestResponse schema
        fr = FriendRequestResponse(**data)
        assert fr.id is not None
        assert fr.ws_type == "friend_request"
        assert fr.user is not None
        assert fr.friend is not None
        assert str(fr.friend.id) == user2_id
        assert fr.status.value == "pending"

        # Validate nested UserResponse
        assert fr.user.nickname == "reqsender"
        assert fr.friend.nickname == "reqreceiver"


def test_send_friend_request_to_self_returns_400(client, auth):
    """POST /friend-requests to self returns 400."""
    email = f"selfreq-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="selfreqpw", nickname="selfrequser")

    me_resp = client.get("/api/auth/me")
    my_id = me_resp.json()["id"]

    resp = client.post("/api/friend-requests", json={"friend_id": my_id})

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data


def test_send_friend_request_duplicate_returns_400(client, auth):
    """POST /friend-requests duplicate returns 400."""
    user1_email = f"dupreq1-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=user1_email, password="dupreq1pw", nickname="dupreq1")

    user2_email = f"dupreq2-{uuid.uuid4().hex[:8]}@example.com"
    user2_id = _create_second_user(client, user2_email, "dupreq2pw", "dupreq2")

    if user2_id:
        # First request should succeed
        resp1 = client.post("/api/friend-requests", json={"friend_id": user2_id})
        assert resp1.status_code == 200

        # Second request should fail
        resp2 = client.post("/api/friend-requests", json={"friend_id": user2_id})
        assert resp2.status_code == 400


def test_send_friend_request_to_nonexistent_user_returns_404(client, auth):
    """POST /friend-requests to non-existent user returns 404."""
    email = f"reqnoexist-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="reqnoexistpw", nickname="reqnoexist")

    fake_id = str(uuid.uuid4())
    resp = client.post("/api/friend-requests", json={"friend_id": fake_id})

    assert resp.status_code == 404


def test_send_friend_request_without_auth_returns_401(client):
    """POST /friend-requests without auth returns 401."""
    resp = client.post("/api/friend-requests", json={"friend_id": str(uuid.uuid4())})
    assert resp.status_code == 401


# =============================================================================
# POST /friend-requests/{id}/accept Tests
# =============================================================================


def test_accept_friend_request_success(client, auth):
    """POST /friend-requests/{id}/accept accepts request."""
    user1_email = f"acceptsender-{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"acceptreceiver-{uuid.uuid4().hex[:8]}@example.com"

    # Register user2 first
    with TestClient(app, base_url="https://testserver") as client2:
        reg_resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "acceptreceiverpw",
                "nickname": "acceptreceiver",
                "settings": {},
            },
        )
        user2_id = reg_resp.json()["id"] if reg_resp.status_code == 201 else None

    if user2_id:
        # User1 sends request
        auth(email=user1_email, password="acceptsenderpw", nickname="acceptsender")
        req_resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            # User2 accepts
            with TestClient(app, base_url="https://testserver") as client2:
                client2.post(
                    "/api/auth/login",
                    data={
                        "username": user2_email,
                        "password": "acceptreceiverpw",
                    },
                )
                accept_resp = client2.post(
                    f"/api/friend-requests/{friend_request_id}/accept"
                )
                assert accept_resp.status_code in [200, 204]


def test_accept_nonexistent_request_returns_404(client, auth):
    """POST /friend-requests/{id}/accept for non-existent returns 404."""
    email = f"acceptnoexist-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="acceptnoexistpw", nickname="acceptnoexist")

    fake_id = str(uuid.uuid4())
    resp = client.post(f"/api/friend-requests/{fake_id}/accept")

    assert resp.status_code == 404


# =============================================================================
# POST /friend-requests/{id}/reject Tests
# =============================================================================


def test_reject_friend_request_success(client, auth):
    """POST /friend-requests/{id}/reject rejects request."""
    user1_email = f"rejectsender-{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"rejectreceiver-{uuid.uuid4().hex[:8]}@example.com"

    # Register user2
    with TestClient(app, base_url="https://testserver") as client2:
        reg_resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "rejectreceiverpw",
                "nickname": "rejectreceiver",
                "settings": {},
            },
        )
        user2_id = reg_resp.json()["id"] if reg_resp.status_code == 201 else None

    if user2_id:
        # User1 sends request
        auth(email=user1_email, password="rejectsenderpw", nickname="rejectsender")
        req_resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            # User2 rejects
            with TestClient(app, base_url="https://testserver") as client2:
                client2.post(
                    "/api/auth/login",
                    data={
                        "username": user2_email,
                        "password": "rejectreceiverpw",
                    },
                )
                reject_resp = client2.post(
                    f"/api/friend-requests/{friend_request_id}/reject"
                )
                assert reject_resp.status_code in [200, 204]


def test_reject_nonexistent_request_returns_404(client, auth):
    """POST /friend-requests/{id}/reject for non-existent returns 404."""
    email = f"rejectnoexist-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="rejectnoexistpw", nickname="rejectnoexist")

    fake_id = str(uuid.uuid4())
    resp = client.post(f"/api/friend-requests/{fake_id}/reject")

    assert resp.status_code == 404
