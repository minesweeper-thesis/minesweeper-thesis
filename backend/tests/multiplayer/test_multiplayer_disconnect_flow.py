import random
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
                "email": f"mp-host-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"mp_host_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"mp-guest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"mp_guest_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_multiplayer_disconnect_flow(
    authenticated_clients: list[AuthenticatedClientBundle],
):
    backup_delay = user_connection_service.REMOVE_OFFLINE_USER_DELAY
    try:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = timedelta(seconds=2)

        random.seed(0)

        host_bundle = authenticated_clients[0]
        guest_bundle = authenticated_clients[1]

        guest_id = guest_bundle.user_id

        create_resp = await host_bundle.http.post("/lobbies")
        assert create_resp.status_code == 200
        lobby_id = create_resp.json()["id"]

        async with AsyncExitStack() as stack:
            host_notif = await stack.enter_async_context(host_bundle.ws())
            guest_notif = await stack.enter_async_context(guest_bundle.ws())
            await receive_type(host_notif, "current_lobby")

            host_lobby = await stack.enter_async_context(
                host_bundle.ws(f"/game/multi/{lobby_id}")
            )
            await receive_type(host_lobby, "session_state")
            await receive_type(host_lobby, "user_ready")

            await receive_type(guest_notif, "current_lobby")

            inv_resp = await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations",
                json={"user_id": guest_id},
            )
            assert inv_resp.status_code == 200

            invitation = await receive_type(guest_notif, "invitation")

            guest_lobby = await stack.enter_async_context(
                guest_bundle.ws(
                    f"/game/multi/{lobby_id}?invitation_id={invitation['id']}"
                )
            )

            await receive_type(guest_lobby, "session_state")
            await receive_type(host_lobby, "invitation_response")
            await receive_type(guest_lobby, "user_ready")
            await receive_type(guest_lobby, "user_ready")
            await receive_type(host_lobby, "user_connection_status")

            await guest_lobby.send_json({"type": "ready"})

            msg = await receive_type(host_lobby, "user_ready")
            assert msg["user_id"] == str(guest_id)
            assert msg["value"] is True
            await receive_type(guest_lobby, "user_ready")

            await guest_notif.close()

            msg = await receive_type(host_lobby, "user_ready")
            assert msg["user_id"] == str(guest_id)
            assert msg["value"] is False

            msg = await receive_type(host_lobby, "user_online_status")
            assert msg["user"]["id"] == str(guest_id)
            assert msg["user"]["is_online"] is False

            msg = await receive_type(host_lobby, "user_connection_status")
            assert msg["user"]["id"] == str(guest_id)
            assert msg["status"] == "disconnected"
    finally:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = backup_delay
