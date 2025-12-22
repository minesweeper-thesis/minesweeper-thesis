import random
import uuid
from contextlib import AsyncExitStack
from datetime import timedelta

import pytest

from backend.tests.multiplayer.ws_helpers import random_cell, receive_type


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
    random.seed(0)

    host_bundle = authenticated_clients[0]
    guest_bundle = authenticated_clients[1]

    guest_id = guest_bundle.user_id

    create_resp = await host_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]
    session_id = lobby_id  # todo

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
        assert await receive_type(host_notif, "current_lobby")
        assert await receive_type(guest_notif, "current_lobby")

        inv_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/invitations",
            json={"user_id": guest_id},
        )
        assert inv_resp.status_code == 200

        invitation = await receive_type(guest_notif, "invitation")
        join_resp = await guest_bundle.http.post(
            f"/lobbies/{lobby_id}/join",
            json={"invitation_id": invitation["id"]},
        )
        assert join_resp.status_code == 200

        host_game = await stack.enter_async_context(
            host_bundle.ws(f"/game/multi/{session_id}")
        )
        guest_game = await stack.enter_async_context(
            guest_bundle.ws(f"/game/multi/{session_id}")
        )

        await receive_type(host_notif, "user_ready")
        await receive_type(host_notif, "user_online_status")
        await receive_type(host_notif, "invitation_response")
        await receive_type(host_notif, "user_connection_status")
        await receive_type(guest_notif, "user_connection_status")

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            assert (await receive_type(ws, "user_ready"))["value"] is True

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            assert (await receive_type(ws, "user_ready"))["value"] is True
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await guest_game.send_json({"type": "not_ready"})
        for ws in (host_notif, guest_notif):
            assert (await receive_type(ws, "user_ready"))["value"] is False

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            assert (await receive_type(ws, "user_ready"))["value"] is True
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))

        start_host = await receive_type(host_game, "round_start")
        await receive_type(guest_game, "round_start")
        start_field = tuple(start_host["start_field"])

        flagged = random_cell(rows=3, cols=3, exclude=start_field)
        await host_game.send_json({"type": "flag", "cell": [flagged[0], flagged[1]]})
        await receive_type(host_game, "flag")

        await host_game.send_json(
            {"type": "reveal_one", "cell": [flagged[0], flagged[1]]}
        )

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_game, guest_game):
            await receive_type(ws, "game_over")

        for ws in (host_game, guest_game):
            await receive_type(ws, "round_end")

        fake_scheduler.reset()

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await receive_type(ws, "user_ready")

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await receive_type(ws, "user_ready")

        for ws in (host_game, guest_game):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await host_game.send_json({"type": "not_ready"})
        for ws in (host_notif, guest_notif):
            msg = await receive_type(ws, "user_ready")
            assert msg["value"] is False

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await receive_type(ws, "user_ready")

        for ws in (host_game, guest_game):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        for ws in (host_game, guest_game):
            start_msg = await receive_type(ws, "round_start")

        start_field = tuple(start_msg["start_field"])
        await guest_game.send_json({"type": "flag", "cell": start_field})
        await receive_type(guest_game, "flag")

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_game, guest_game):
            await receive_type(ws, "game_over")

        for ws in (host_game, guest_game):
            await receive_type(ws, "round_end")

        fake_scheduler.reset()

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await receive_type(ws, "user_ready")

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await receive_type(ws, "user_ready")

        for ws in (host_game, guest_game):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        for ws in (host_game, guest_game):
            await receive_type(ws, "round_start")

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_game, guest_game):
            await receive_type(ws, "game_over")

        for ws in (host_game, guest_game):
            await receive_type(ws, "round_end")

        for ws in (host_game, guest_game):
            await receive_type(ws, "session_over")
