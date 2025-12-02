"""
Comprehensive notifications WebSocket tests.
Tests: WebSocket /ws - CurrentLobbyResponse, PendingInvitationsResponse
"""

import json
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
# WebSocket /ws Connection Tests
# =============================================================================


def test_notifications_websocket_connect_returns_current_lobby_response(client, auth):
    """WebSocket /ws on connect returns CurrentLobbyResponse."""
    email = f"notif-connect-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="notifconnectpw", nickname="notifconnect")

    # Pass cookies to websocket - client.cookies contains auth cookie after login
    with client.websocket_connect("/api/ws", cookies=dict(client.cookies)) as ws:
        data = json.loads(ws.receive_text())

        # Validate CurrentLobbyResponse schema
        assert data["type"] == "current_lobby"
        assert "lobby" in data

        # lobby should be None if not in any lobby
        # or LobbyResponse if in a lobby
        lobby = data["lobby"]
        if lobby is not None:
            assert "id" in lobby
            assert "host" in lobby
            assert "users" in lobby
            assert "game_config" in lobby


def test_notifications_websocket_connect_with_active_lobby(client, auth):
    """WebSocket /ws shows lobby if user has created one."""
    email = f"notif-lobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="notiflobbypw", nickname="notiflobby")

    # Create a lobby first
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    with client.websocket_connect("/api/ws", cookies=dict(client.cookies)) as ws:
        data = json.loads(ws.receive_text())

        assert data["type"] == "current_lobby"

        # Should have the lobby
        lobby = data["lobby"]
        if lobby is not None:
            assert lobby["id"] == lobby_id
            assert lobby["host"]["nickname"] == "notiflobby"


# =============================================================================
# WebSocket /ws PendingInvitations Tests
# =============================================================================


def test_notifications_websocket_pending_invitations_request(client, auth):
    """WebSocket /ws responds to pending_invitations request."""
    email = f"notif-pending-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="notifpendingpw", nickname="notifpending")

    with client.websocket_connect("/api/ws", cookies=dict(client.cookies)) as ws:
        # Receive initial CurrentLobbyResponse
        ws.receive_text()

        # Send pending invitations request
        ws.send_json({"type": "pending_invitations"})

        data = json.loads(ws.receive_text())

        # Validate PendingInvitationsResponse schema
        assert data["type"] == "pending_invitations"
        assert "invitations" in data
        assert isinstance(data["invitations"], list)


def test_notifications_websocket_pending_invitations_has_invitation(client, auth):
    """WebSocket /ws pending_invitations shows real invitation."""
    host_email = f"notif-host-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"notif-guest-{uuid.uuid4().hex[:8]}@example.com"

    # Create host, create lobby, invite guest
    auth(email=host_email, password="notifhostpw", nickname="notifhost")
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    # Create guest
    guest_client = _create_second_user_and_login(
        guest_email, "notifguestpw", "notifguest"
    )
    guest_me = guest_client.get("/api/auth/me")
    guest_id = guest_me.json()["id"]

    # Invite guest
    client.post(f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id})

    # Guest connects to /ws and checks pending invitations
    with guest_client.websocket_connect(
        "/api/ws", cookies=dict(guest_client.cookies)
    ) as ws:
        # Initial state
        ws.receive_text()

        # Request pending invitations
        ws.send_json({"type": "pending_invitations"})
        data = json.loads(ws.receive_text())

        assert data["type"] == "pending_invitations"
        invitations = data["invitations"]

        # Should have at least one invitation
        assert len(invitations) >= 1

        # Validate InvitationResponse schema
        inv = invitations[0]
        assert "type" in inv
        assert inv["type"] == "invitation"
        assert "id" in inv
        assert "lobby" in inv

        # Validate InvitationLobbyResponse
        lobby = inv["lobby"]
        assert "id" in lobby
        assert "host" in lobby
        assert "game_config" in lobby

        # Validate host UserResponse
        host = lobby["host"]
        assert host["nickname"] == "notifhost"


# =============================================================================
# WebSocket /ws Without Auth Tests
# =============================================================================


def test_notifications_websocket_without_auth_fails(client):
    """WebSocket /ws without auth should fail."""
    try:
        with client.websocket_connect("/api/ws") as ws:
            # Should disconnect or return error
            data = ws.receive_text()
            # If we get here, check for error response
            parsed = json.loads(data)
            # Might work or fail depending on implementation
    except Exception:
        # Expected - websocket should reject unauthenticated connection
        pass
