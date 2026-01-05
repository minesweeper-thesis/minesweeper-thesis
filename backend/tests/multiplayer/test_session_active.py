import uuid
from contextlib import AsyncExitStack
from datetime import datetime, timedelta

import pytest
from httpx_ws import WebSocketDisconnect

from backend.tests.multiplayer.ws_helpers import receive_type


@pytest.mark.time_machine(datetime.now())
@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"session-host-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"session_host_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"session-guest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"session_guest_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_update_lobby_blocked_when_session_active(
    authenticated_clients, fake_scheduler
):
    host_client = authenticated_clients[0]

    create_resp = await host_client.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]

    initial_config = {
        "rounds": 3,
        "max_round_time": 60,
        "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 3},
        "game_mode": "normal",
        "generator": {"type": "random", "settings": None},
    }

    resp = await host_client.http.put(f"/lobbies/{lobby_id}", json=initial_config)
    assert resp.status_code in [200, 204]

    async with AsyncExitStack() as stack:
        lobby_ws = await stack.enter_async_context(
            host_client.ws(f"/game/multi/{lobby_id}")
        )

        await receive_type(lobby_ws, "session_state")
        await receive_type(lobby_ws, "user_ready")

        await lobby_ws.send_json({"type": "ready"})
        await receive_type(lobby_ws, "user_ready")
        await receive_type(lobby_ws, "round_ready")
        await receive_type(lobby_ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=6))

        updated_config = {
            "rounds": 5,
            "max_round_time": 120,
            "difficulty_level": {"rows": 10, "columns": 10, "mine_count": 15},
            "game_mode": "hardcore",
            "generator": {"type": "random", "settings": None},
        }

        resp = await host_client.http.put(f"/lobbies/{lobby_id}", json=updated_config)
        assert resp.status_code == 400
        assert "active session" in resp.json().get("detail", "").lower()


@pytest.mark.time_machine(datetime.now())
@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"join-host-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"join_host_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"join-guest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"join_guest_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_join_lobby_blocked_when_session_active(
    authenticated_clients, fake_scheduler
):
    host_client = authenticated_clients[0]
    guest_client = authenticated_clients[1]
    guest_id = guest_client.user_id

    create_resp = await host_client.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]

    async with AsyncExitStack() as stack:
        host_notif = await stack.enter_async_context(host_client.ws())
        guest_notif = await stack.enter_async_context(guest_client.ws())

        host_lobby = await stack.enter_async_context(
            host_client.ws(f"/game/multi/{lobby_id}")
        )

        await receive_type(host_notif, "current_lobby")
        await receive_type(guest_notif, "current_lobby")

        await receive_type(host_lobby, "session_state")
        await receive_type(host_lobby, "user_ready")

        inv_resp = await host_client.http.post(
            f"/lobbies/{lobby_id}/invitations",
            json={"user_id": guest_id},
        )
        assert inv_resp.status_code == 200

        invitation = await receive_type(guest_notif, "invitation")

        await host_lobby.send_json({"type": "ready"})
        await receive_type(host_lobby, "user_ready")
        await receive_type(host_lobby, "round_ready")
        await receive_type(host_lobby, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=6))

        try:
            guest_lobby = guest_client.ws(
                f"/game/multi/{lobby_id}?invitation_id={invitation['id']}"
            )
            await stack.enter_async_context(guest_lobby)
        except* WebSocketDisconnect as group:
            assert "session is active" in group.exceptions[0].reason  # type: ignore[misc]
