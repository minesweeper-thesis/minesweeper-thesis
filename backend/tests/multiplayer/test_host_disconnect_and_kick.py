import uuid
from contextlib import AsyncExitStack
from datetime import timedelta

import pytest

from backend.services.user import user_connection_service
from backend.tests.conftest import AuthenticatedClientBundle
from backend.tests.multiplayer.ws_helpers import receive_type


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"host-disconnect-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"host_disconnect_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"guest-disco-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"guest_disco_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"guest2-disco-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"guest2_disco_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_host_disconnect_broadcasts_new_host_message(
    authenticated_clients: list[AuthenticatedClientBundle],
):
    backup_delay = user_connection_service.REMOVE_OFFLINE_USER_DELAY
    try:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = timedelta(seconds=2)
        host_bundle = authenticated_clients[0]
        guest1_bundle = authenticated_clients[1]
        guest2_bundle = authenticated_clients[2]

        g1_id = guest1_bundle.user_id
        g2_id = guest2_bundle.user_id

        create_resp = await host_bundle.http.post("/lobbies")
        assert create_resp.status_code == 200
        lobby_id = create_resp.json()["id"]

        async with AsyncExitStack() as stack:
            host_notif = await stack.enter_async_context(host_bundle.ws())
            await receive_type(host_notif, "current_lobby")

            host_lobby = await stack.enter_async_context(
                host_bundle.ws(f"/game/multi/{lobby_id}")
            )
            await receive_type(host_lobby, "session_state")
            await receive_type(host_lobby, "user_ready")

            g1_notif = await stack.enter_async_context(guest1_bundle.ws())
            await receive_type(g1_notif, "current_lobby")

            inv1_resp = await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations", json={"user_id": g1_id}
            )
            assert inv1_resp.status_code == 200
            inv1 = await receive_type(g1_notif, "invitation")

            g1_lobby = await stack.enter_async_context(
                guest1_bundle.ws(f"/game/multi/{lobby_id}?invitation_id={inv1['id']}")
            )
            await receive_type(g1_lobby, "session_state")
            await receive_type(g1_lobby, "user_ready")
            await receive_type(g1_lobby, "user_ready")
            await receive_type(host_lobby, "invitation_response")
            await receive_type(host_lobby, "user_connection_status")

            g2_notif = await stack.enter_async_context(guest2_bundle.ws())
            await receive_type(g2_notif, "current_lobby")

            inv2_resp = await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations", json={"user_id": g2_id}
            )
            assert inv2_resp.status_code == 200
            inv2 = await receive_type(g2_notif, "invitation")

            g2_lobby = await stack.enter_async_context(
                guest2_bundle.ws(f"/game/multi/{lobby_id}?invitation_id={inv2['id']}")
            )
            await receive_type(g2_lobby, "session_state")
            await receive_type(g2_lobby, "user_ready")
            await receive_type(g2_lobby, "user_ready")
            await receive_type(g2_lobby, "user_ready")
            await receive_type(g1_lobby, "user_connection_status")
            await receive_type(host_lobby, "invitation_response")
            await receive_type(host_lobby, "user_connection_status")

            await host_notif.close()

            for ws in (g1_lobby, g2_lobby):
                offline_msg = await receive_type(ws, "user_online_status")
                assert offline_msg["user"]["id"] == str(host_bundle.user_id)
                assert offline_msg["user"]["is_online"] is False

            for ws in (g1_lobby, g2_lobby):
                offline_msg = await receive_type(ws, "user_connection_status")
                assert offline_msg["user"]["id"] == str(host_bundle.user_id)
                assert offline_msg["status"] == "disconnected"

            for ws in (g1_lobby, g2_lobby):
                await receive_type(ws, "user_ready")
                await receive_type(ws, "user_ready")

            for ws in (g1_lobby, g2_lobby):
                new_host_msg = await receive_type(ws, "new_host")
                assert "host" in new_host_msg
                host_id = new_host_msg["host"]["id"]
                assert host_id == str(g1_id) or host_id == str(g2_id)

            await g1_notif.close()

            g1_notif = await stack.enter_async_context(guest1_bundle.ws())
            lobby_msg = await receive_type(g1_notif, "current_lobby")
            assert lobby_msg["lobby"]["host"]["id"] == host_id

    finally:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = backup_delay


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"kick-self-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"kick_self_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"guest-kick-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"guest_kick_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_host_cannot_kick_themselves(
    authenticated_clients: list[AuthenticatedClientBundle],
):
    host_bundle = authenticated_clients[0]
    guest_bundle = authenticated_clients[1]

    host_id = host_bundle.user_id
    guest_id = guest_bundle.user_id

    create_resp = await host_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]

    async with AsyncExitStack() as stack:
        guest_notif = await stack.enter_async_context(guest_bundle.ws())
        await receive_type(guest_notif, "current_lobby")

        inv_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
        )
        assert inv_resp.status_code == 200
        inv = await receive_type(guest_notif, "invitation")

        guest_lobby = await stack.enter_async_context(
            guest_bundle.ws(f"/game/multi/{lobby_id}?invitation_id={inv['id']}")
        )
        await receive_type(guest_lobby, "session_state")
        await receive_type(guest_lobby, "user_ready")
        await receive_type(guest_lobby, "user_ready")

        kick_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/kick",
            json={"user_id": host_id},
        )
        assert kick_resp.status_code == 400
