import json

import pytest


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": "notif-pending@example.com",
                "password": "pw",
                "nickname": "notifpending",
            },
            {
                "email": "notif-guest@example.com",
                "password": "pw",
                "nickname": "notifguest",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_notifications_websocket_pending_invitations_request(
    authenticated_clients,
):
    bundle = authenticated_clients[0]

    with bundle.get_ws() as ws:
        ws.receive_text()

        ws.send_json({"type": "pending_invitations"})

        data = json.loads(ws.receive_text())

    assert data["type"] == "pending_invitations"
    assert "invitations" in data
    assert isinstance(data["invitations"], list)


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": "notif-host@example.com",
                "password": "pw",
                "nickname": "notifhost",
            },
            {
                "email": "notif-guest2@example.com",
                "password": "pw",
                "nickname": "notifguest2",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_notifications_websocket_pending_invitations_has_invitation(
    authenticated_clients,
):
    from backend.tests.utils.cookies import using_auth_cookie

    host_bundle = authenticated_clients[0]
    guest_bundle = authenticated_clients[1]

    async with using_auth_cookie(host_bundle.http, host_bundle.auth_cookie):
        create_resp = await host_bundle.http.post("/api/lobbies")
        lobby_id = create_resp.json()["id"]

    async with using_auth_cookie(host_bundle.http, host_bundle.auth_cookie):
        guest_me = await guest_bundle.http.get("/api/auth/me")
        guest_id = guest_me.json()["id"]

        await host_bundle.http.post(
            f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
        )

    with guest_bundle.get_ws() as ws:
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
