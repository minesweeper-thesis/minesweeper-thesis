import json
import uuid

from backend.tests.utils.test_helpers import create_second_user_and_login


def test_notifications_websocket_pending_invitations_request(client, auth):
    email = f"notif-pending-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="notifpendingpw", nickname="notifpending")

    with client.websocket_connect("/api/ws", cookies=dict(client.cookies)) as ws:
        ws.receive_text()

        ws.send_json({"type": "pending_invitations"})

        data = json.loads(ws.receive_text())

        assert data["type"] == "pending_invitations"
        assert "invitations" in data
        assert isinstance(data["invitations"], list)


def test_notifications_websocket_pending_invitations_has_invitation(client, auth):
    host_email = f"notif-host-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"notif-guest-{uuid.uuid4().hex[:8]}@example.com"

    auth(email=host_email, password="notifhostpw", nickname="notifhost")
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_client = create_second_user_and_login(
        guest_email, "notifguestpw", "notifguest"
    )
    guest_me = guest_client.get("/api/auth/me")
    guest_id = guest_me.json()["id"]

    client.post(f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id})

    with guest_client.websocket_connect(
        "/api/ws", cookies=dict(guest_client.cookies)
    ) as ws:
        ws.receive_text()

        ws.send_json({"type": "pending_invitations"})
        data = json.loads(ws.receive_text())

        assert data["type"] == "pending_invitations"
        invitations = data["invitations"]

        assert len(invitations) >= 1

        inv = invitations[0]
        assert "type" in inv
        assert inv["type"] == "invitation"
        assert "id" in inv
        assert "lobby" in inv

        lobby = inv["lobby"]
        assert "id" in lobby
        assert "host" in lobby
        assert "game_config" in lobby

        host = lobby["host"]
        assert host["nickname"] == "notifhost"
