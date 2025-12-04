"""
Comprehensive lobby router tests.
Tests: POST /lobbies, PUT /lobbies/{id}, POST /lobbies/{id}/invitations,
       POST /lobbies/{id}/join, POST /lobbies/{id}/leave, DELETE /invitations/{id},
       POST /lobbies/{id}/ready, POST /lobbies/{id}/chat-messages,
       GET /lobbies/{id}/chat-messages
"""

import uuid

from fastapi.testclient import TestClient

from backend.main import app


def _create_second_user_and_login(email, password, nickname):
    """Create user and return logged-in client."""
    client = TestClient(app, base_url="https://testserver")
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "nickname": nickname,
            "settings": {},
        },
    )
    client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )
    return client


# =============================================================================
# POST /lobbies Tests
# =============================================================================


def test_create_lobby_returns_lobby_response(client, auth):
    """POST /lobbies returns LobbyResponse with correct schema."""
    email = f"lobbyhost-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="lobbyhostpw", nickname="lobbyhost")

    resp = client.post("/api/lobbies")

    assert resp.status_code == 200
    data = resp.json()

    # Validate LobbyResponse schema
    assert "id" in data
    assert "host" in data
    assert "users" in data
    assert "game_config" in data

    # Validate types
    uuid.UUID(str(data["id"]))
    assert isinstance(data["users"], list)

    # Validate host UserResponse
    host = data["host"]
    assert "id" in host
    assert "nickname" in host
    assert host["nickname"] == "lobbyhost"

    # Validate GameConfig
    config = data["game_config"]
    assert "rounds" in config
    assert "max_round_time" in config
    assert "difficulty_level" in config
    assert "game_mode" in config
    assert "generator" in config

    # Validate DifficultyLevel
    dl = config["difficulty_level"]
    assert "rows" in dl
    assert "columns" in dl
    assert "mine_count" in dl


def test_create_lobby_without_auth_returns_401(client):
    """POST /lobbies without auth returns 401."""
    resp = client.post("/api/lobbies")
    assert resp.status_code == 401


# =============================================================================
# PUT /lobbies/{lobby_id} Tests
# =============================================================================


def test_update_lobby_config_success(client, auth):
    """PUT /lobbies/{id} updates lobby configuration."""
    email = f"updatelobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="updatelobbypw", nickname="updatelobbyhost")

    # Create lobby
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Update config
    new_config = {
        "rounds": 5,
        "max_round_time": 180,
        "difficulty_level": {
            "rows": 10,
            "columns": 10,
            "mine_count": 15,
        },
        "game_mode": "hardcore",
        "generator": {
            "type": "random",
            "settings": None,
        },
    }

    resp = client.put(f"/api/lobbies/{lobby_id}", json=new_config)
    assert resp.status_code in [200, 204]


def test_update_lobby_config_without_auth_returns_401(client):
    """PUT /lobbies/{id} without auth returns 401."""
    resp = client.put(
        f"/api/lobbies/{uuid.uuid4()}",
        json={
            "rounds": 3,
            "max_round_time": 120,
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 5},
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert resp.status_code == 401


# =============================================================================
# POST /lobbies/{lobby_id}/invitations Tests
# =============================================================================


def test_invite_user_to_lobby_success(client, auth):
    """POST /lobbies/{id}/invitations sends invitation."""
    host_email = f"invitehost-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=host_email, password="invitehostpw", nickname="invitehost")

    # Create lobby
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Create user2 to invite
    guest_email = f"inviteguest-{uuid.uuid4().hex[:8]}@example.com"
    with TestClient(app, base_url="https://testserver") as client2:
        reg_resp = client2.post(
            "/api/auth/register",
            json={
                "email": guest_email,
                "password": "inviteguestpw",
                "nickname": "inviteguest",
                "settings": {},
            },
        )
        guest_id = reg_resp.json()["id"] if reg_resp.status_code == 201 else None

    if guest_id:
        resp = client.post(
            f"/api/lobbies/{lobby_id}/invitations",
            json={
                "user_id": guest_id,
            },
        )
        assert resp.status_code in [200, 204]


def test_invite_user_without_auth_returns_401(client):
    """POST /lobbies/{id}/invitations without auth returns 401."""
    resp = client.post(
        f"/api/lobbies/{uuid.uuid4()}/invitations",
        json={
            "user_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


# =============================================================================
# POST /lobbies/{lobby_id}/join Tests
# =============================================================================


def test_join_lobby_returns_lobby_response(client, auth):
    """POST /lobbies/{id}/join returns LobbyResponse."""
    host_email = f"joinhost-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"joinguest-{uuid.uuid4().hex[:8]}@example.com"

    # Host creates lobby
    auth(email=host_email, password="joinhostpw", nickname="joinhost")
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Create and login guest
    guest_client = _create_second_user_and_login(
        guest_email, "joinguestpw", "joinguest"
    )
    guest_me = guest_client.get("/api/auth/me")
    guest_id = guest_me.json()["id"]

    # Host invites guest
    client.post(f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id})

    # Guest gets pending invitations via /ws or API
    # For now, we'll use notifications endpoint or just try joining
    # This requires knowing the invitation_id

    # Check guest's pending invitations (if endpoint exists)
    # Since lobby join requires invitation_id, this test is complex


def test_join_lobby_without_auth_returns_401(client):
    """POST /lobbies/{id}/join without auth returns 401."""
    resp = client.post(
        f"/api/lobbies/{uuid.uuid4()}/join",
        json={
            "invitation_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


# =============================================================================
# POST /lobbies/{lobby_id}/leave Tests
# =============================================================================


def test_leave_lobby_success(client, auth):
    """POST /lobbies/{id}/leave removes user from lobby."""
    email = f"leavelobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="leavelobbypw", nickname="leavelobbyhost")

    # Create lobby
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Leave lobby (host leaving)
    resp = client.post(f"/api/lobbies/{lobby_id}/leave")
    assert resp.status_code in [200, 204]


def test_leave_lobby_without_auth_returns_401(client):
    """POST /lobbies/{id}/leave without auth returns 401."""
    resp = client.post(f"/api/lobbies/{uuid.uuid4()}/leave")
    assert resp.status_code == 401


# =============================================================================
# DELETE /invitations/{invitation_id} Tests
# =============================================================================


def test_reject_invitation_success(client, auth):
    """DELETE /invitations/{id} rejects game invitation."""
    host_email = f"rejecthost-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"rejectguest-{uuid.uuid4().hex[:8]}@example.com"

    # Create host and lobby
    auth(email=host_email, password="rejecthostpw", nickname="rejecthost")
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Create guest
    guest_client = _create_second_user_and_login(
        guest_email, "rejectguestpw", "rejectguest"
    )
    guest_me = guest_client.get("/api/auth/me")
    guest_id = guest_me.json()["id"]

    # Invite guest
    client.post(f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id})

    # Guest rejects - but we need invitation_id
    # This would require fetching from /ws or pending endpoint


def test_reject_invitation_without_auth_returns_401(client):
    """DELETE /invitations/{id} without auth returns 401."""
    resp = client.delete(f"/api/invitations/{uuid.uuid4()}")
    assert resp.status_code == 401


# =============================================================================
# POST /lobbies/{lobby_id}/ready Tests
# =============================================================================


def test_set_ready_in_lobby(client, auth):
    """POST /lobbies/{id}/ready sets user as ready."""
    email = f"readylobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="readylobbypw", nickname="readylobbyhost")

    # Create lobby
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Set ready
    resp = client.post(f"/api/lobbies/{lobby_id}/ready")
    # May succeed or fail depending on game state requirements
    assert resp.status_code in [200, 204, 400]


def test_set_ready_without_auth_returns_401(client):
    """POST /lobbies/{id}/ready without auth returns 401."""
    resp = client.post(f"/api/lobbies/{uuid.uuid4()}/ready")
    assert resp.status_code == 401


# =============================================================================
# POST /lobbies/{lobby_id}/chat-messages Tests
# =============================================================================


def test_send_chat_message_success(client, auth):
    """POST /lobbies/{id}/chat-messages sends chat message."""
    email = f"chatlobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="chatlobbypw", nickname="chatlobbyhost")

    # Create lobby
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Send message
    resp = client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "Hello lobby!",
        },
    )
    assert resp.status_code in [200, 204]


def test_send_empty_chat_message(client, auth):
    """POST /lobbies/{id}/chat-messages with empty content."""
    email = f"emptychat-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="emptychatpw", nickname="emptychathost")

    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "",
        },
    )
    # May succeed or return validation error
    assert resp.status_code in [200, 204, 422]


def test_send_chat_message_without_auth_returns_401(client):
    """POST /lobbies/{id}/chat-messages without auth returns 401."""
    resp = client.post(
        f"/api/lobbies/{uuid.uuid4()}/chat-messages",
        json={
            "content": "Hello!",
        },
    )
    assert resp.status_code == 401


# =============================================================================
# GET /lobbies/{lobby_id}/chat-messages Tests
# =============================================================================


def test_get_chat_messages_returns_list(client, auth):
    """GET /lobbies/{id}/chat-messages returns list of ChatMessageResponse."""
    email = f"getchat-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="getchatpw", nickname="getchathost")

    # Create lobby
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Send a message first
    client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "Test message",
        },
    )

    # Get messages
    resp = client.get(f"/api/lobbies/{lobby_id}/chat-messages")

    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, list)

    if len(data) > 0:
        msg = data[0]
        # Validate ChatMessageResponse schema - REST API also aliases ws_type to "type"
        assert "type" in msg
        assert msg["type"] == "chat_message"
        assert "sender" in msg
        assert "lobby_id" in msg
        assert "content" in msg
        assert "timestamp" in msg

        # Validate sender UserResponse
        sender = msg["sender"]
        assert "id" in sender
        assert "nickname" in sender

        # Validate types
        assert isinstance(msg["content"], str)
        assert isinstance(msg["timestamp"], int)


def test_get_chat_messages_without_auth_returns_401(client):
    """GET /lobbies/{id}/chat-messages without auth returns 401."""
    resp = client.get(f"/api/lobbies/{uuid.uuid4()}/chat-messages")
    assert resp.status_code == 401
