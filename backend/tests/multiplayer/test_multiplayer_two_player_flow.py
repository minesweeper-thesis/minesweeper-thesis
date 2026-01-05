import uuid
from contextlib import AsyncExitStack
from datetime import datetime, timedelta

import pytest

from backend.tests.multiplayer.ws_helpers import random_cell, receive_type


@pytest.mark.time_machine(datetime.now())
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
async def test_multiplayer_two_player_flow(authenticated_clients, fake_scheduler):
    host_bundle = authenticated_clients[0]
    guest_bundle = authenticated_clients[1]

    guest_id = guest_bundle.user_id

    create_resp = await host_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]

    update_resp = await host_bundle.http.put(
        f"/lobbies/{lobby_id}",
        json={
            "rounds": 3,
            "max_round_time": 2,
            "difficulty_level": {"rows": 3, "columns": 3, "mine_count": 3},
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert update_resp.status_code == 200

    async with AsyncExitStack() as stack:
        host_notif = await stack.enter_async_context(host_bundle.ws())
        guest_notif = await stack.enter_async_context(guest_bundle.ws())
        await receive_type(host_notif, "current_lobby")
        await receive_type(guest_notif, "current_lobby")

        host_lobby = await stack.enter_async_context(
            host_bundle.ws(f"/game/multi/{lobby_id}")
        )
        await receive_type(host_lobby, "session_state")
        await receive_type(host_lobby, "user_ready")

        inv_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/invitations",
            json={"user_id": guest_id},
        )
        assert inv_resp.status_code == 200

        invitation = await receive_type(guest_notif, "invitation")

        guest_lobby = await stack.enter_async_context(
            guest_bundle.ws(f"/game/multi/{lobby_id}?invitation_id={invitation['id']}")
        )
        await receive_type(guest_lobby, "session_state")
        await receive_type(host_lobby, "invitation_response")
        await receive_type(guest_lobby, "user_ready")
        await receive_type(guest_lobby, "user_ready")

        await receive_type(host_lobby, "user_connection_status")

        await host_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            assert (await receive_type(ws, "user_ready"))["value"] is True

        await guest_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            assert (await receive_type(ws, "user_ready"))["value"] is True
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await guest_lobby.send_json({"type": "not_ready"})
        for ws in (host_lobby, guest_lobby):
            assert (await receive_type(ws, "user_ready"))["value"] is False

        await guest_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            assert (await receive_type(ws, "user_ready"))["value"] is True
            msg = await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))

        start_host = await receive_type(host_lobby, "round_start")
        await receive_type(guest_lobby, "round_start")
        start_field = tuple(start_host["start_field"])

        flagged = random_cell(rows=3, cols=3, exclude=start_field)
        await host_lobby.send_json({"type": "flag", "cell": [flagged[0], flagged[1]]})
        await receive_type(host_lobby, "flag")

        await host_lobby.send_json(
            {"type": "reveal_one", "cell": [flagged[0], flagged[1]]}
        )

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "game_over")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "score_update")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "score_update")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "round_end")

        await host_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "user_ready")

        await guest_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "user_ready")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await host_lobby.send_json({"type": "not_ready"})
        for ws in (host_lobby, guest_lobby):
            msg = await receive_type(ws, "user_ready")
            assert msg["value"] is False

        await host_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "user_ready")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        for ws in (host_lobby, guest_lobby):
            start_msg = await receive_type(ws, "round_start")

        start_field = tuple(start_msg["start_field"])
        await guest_lobby.send_json({"type": "flag", "cell": start_field})
        await receive_type(guest_lobby, "flag")

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "game_over")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "score_update")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "score_update")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "round_end")

        await host_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "user_ready")

        await guest_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "user_ready")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "round_start")

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "game_over")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "score_update")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "score_update")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "round_end")

        for ws in (host_lobby, guest_lobby):
            await receive_type(ws, "session_over")
