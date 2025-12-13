import json
import uuid

import pytest

from backend.tests.utils.cookies import using_auth_cookie
from backend.tests.utils.test_helpers import create_second_user_and_login


@pytest.mark.anyio
async def test_notifications_websocket_pending_invitations_request(client, auth):
    email = f"notif-pending-{uuid.uuid4().hex[:8]}@example.com"
    user = await auth(email=email, password="notifpendingpw", nickname="notifpending")

    async with using_auth_cookie(client, user["auth_cookie"]):
        with client.websocket_connect("/api/ws") as ws:
            ws.receive_text()

            ws.send_json({"type": "pending_invitations"})

            data = json.loads(ws.receive_text())

        assert data["type"] == "pending_invitations"
        assert "invitations" in data
        assert isinstance(data["invitations"], list)


@pytest.mark.anyio
async def test_notifications_websocket_pending_invitations_has_invitation(client, auth):
    host_email = f"notif-host-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"notif-guest-{uuid.uuid4().hex[:8]}@example.com"

    await auth(email=host_email, password="notifhostpw", nickname="notifhost")
    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    with create_second_user_and_login(
        guest_email, "notifguestpw", "notifguest"
    ) as guest_client:
        guest_me = guest_client.get("/api/auth/me")
        guest_id = guest_me.json()["id"]

        await client.post(
            f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
        )

        guest_auth_cookie = next(
            (c.value for c in guest_client.cookies.jar if c.name == "auth"), None
        )
        assert guest_auth_cookie, "Guest login did not set 'auth' cookie"

        async with using_auth_cookie(guest_client, guest_auth_cookie):
            with guest_client.websocket_connect("/api/ws") as ws:
                await ws.receive_text()

                await ws.send_json({"type": "pending_invitations"})
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
