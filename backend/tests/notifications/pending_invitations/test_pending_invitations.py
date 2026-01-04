import uuid

import pytest

from backend.tests.conftest import AuthenticatedClientBundle


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"notif-pending-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"notifpending_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"notif-guest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"notifguest_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_notifications_websocket_pending_invitations_request(
    authenticated_clients,
):
    bundle = authenticated_clients[0]

    async with bundle.ws() as ws:
        await ws.receive_json()

        await ws.send_json({"type": "pending_invitations"})

        data = await ws.receive_json()

    assert data["type"] == "pending_invitations"
    assert "invitations" in data
    assert isinstance(data["invitations"], list)


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"notif-host-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"notifhost_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"notif-guest2-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"notifguest2_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_notifications_websocket_pending_invitations_has_invitation(
    authenticated_clients: list[AuthenticatedClientBundle],
):
    host_bundle = authenticated_clients[0]
    guest_bundle = authenticated_clients[1]

    create_resp = await host_bundle.http.post("/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_id = guest_bundle.user_id

    await host_bundle.http.post(
        f"/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
    )

    async with guest_bundle.ws() as ws:
        await ws.receive_json()

        await ws.send_json({"type": "pending_invitations"})
        data = await ws.receive_json()

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
        assert "notifhost_" in host["nickname"]
