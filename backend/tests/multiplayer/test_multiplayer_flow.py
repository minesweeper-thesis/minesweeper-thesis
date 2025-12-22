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
                "email": f"mp-g1-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"mp_g1_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"mp-g2-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"mp_g2_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_multiplayer_full_flow_many_players(
    authenticated_clients, fake_scheduler, background_handler_override
):
    random.seed(0)

    host_bundle = authenticated_clients[0]
    g1_bundle = authenticated_clients[1]
    g2_bundle = authenticated_clients[2]

    create_resp = await host_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]
    session_id = lobby_id

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
    assert update_resp.status_code in [200, 204]

    g1_id = g1_bundle.user_id
    g2_id = g2_bundle.user_id

    async with AsyncExitStack() as stack:
        host_notif = await stack.enter_async_context(host_bundle.ws())
        g1_notif = await stack.enter_async_context(g1_bundle.ws())
        g2_notif = await stack.enter_async_context(g2_bundle.ws())

        assert await receive_type(host_notif, "current_lobby")
        assert await receive_type(g1_notif, "current_lobby")
        assert await receive_type(g2_notif, "current_lobby")

        await receive_type(host_notif, "user_ready")
        await receive_type(host_notif, "user_online_status")

        inv_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/invitations",
            json={"user_id": g1_id},
        )
        assert inv_resp.status_code == 200

        inv1 = await receive_type(g1_notif, "invitation")
        join_resp = await g1_bundle.http.post(
            f"/lobbies/{lobby_id}/join",
            json={"invitation_id": inv1["id"]},
        )
        assert join_resp.status_code == 200

        inv_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/invitations",
            json={"user_id": g2_id},
        )
        assert inv_resp.status_code == 200
        inv2 = await receive_type(g2_notif, "invitation")
        join_resp = await g2_bundle.http.post(
            f"/lobbies/{lobby_id}/join",
            json={"invitation_id": inv2["id"]},
        )
        assert join_resp.status_code == 200

        host_game = await stack.enter_async_context(
            host_bundle.ws(f"/game/multi/{session_id}")
        )
        g1_game = await stack.enter_async_context(
            g1_bundle.ws(f"/game/multi/{session_id}")
        )
        g2_game = await stack.enter_async_context(
            g2_bundle.ws(f"/game/multi/{session_id}")
        )

        await receive_type(host_notif, "invitation_response")
        await receive_type(host_notif, "user_connection_status")
        await receive_type(host_notif, "invitation_response")
        await receive_type(host_notif, "user_connection_status")

        await receive_type(g1_notif, "user_connection_status")
        await receive_type(g1_notif, "user_connection_status")
        await receive_type(g2_notif, "user_connection_status")

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        await g2_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        for ws in (host_notif, g1_notif, g2_notif):
            await receive_type(ws, "round_ready")

        for ws in (host_notif, g1_notif, g2_notif):
            await receive_type(ws, "round_countdown")

        await g1_game.send_json({"type": "not_ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is False

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        for ws in (host_notif, g1_notif, g2_notif):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))

        starts = [
            await receive_type(ws, "round_start")
            for ws in (host_game, g1_game, g2_game)
        ]
        start_field = tuple(starts[0]["start_field"])

        await host_game.send_json(
            {"type": "reveal_one", "cell": [start_field[0], start_field[1]]}
        )
        await receive_type(host_game, "reveal")
        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "score_update")

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        await host_game.send_json({"type": "flag", "cell": [cell[0], cell[1]]})
        await receive_type(host_game, "flag")

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        await g1_game.send_json({"type": "flag", "cell": [cell[0], cell[1]]})
        await receive_type(g1_game, "flag")

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "game_over")
            await receive_type(ws, "round_end")

        fake_scheduler.reset()

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        await g1_game.send_json({"type": "not_ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is False

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        await g2_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        for ws in (host_game, g1_game, g2_game):
            start_msg = await receive_type(ws, "round_start")

        start_field = tuple(start_msg["start_field"])

        await host_game.send_json({"type": "reveal_one", "cell": start_field})
        await receive_type(host_game, "reveal")

        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "score_update")

        await g1_game.send_json({"type": "reveal_one", "cell": start_field})
        await receive_type(g1_game, "reveal")

        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "score_update")

        await g2_game.send_json({"type": "reveal_one", "cell": start_field})
        await receive_type(g2_game, "reveal")

        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "score_update")

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "game_over")

        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "round_end")

        fake_scheduler.reset()

        for ws in (host_game, g1_game, g2_game):
            await ws.send_json({"type": "ready"})

        for ws in (host_notif, g1_notif, g2_notif):
            ready_msg = await receive_type(ws, "user_ready")
            assert ready_msg["value"] is True

        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "round_ready")
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "round_start")

        await fake_scheduler.skip(timedelta(seconds=60))
        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "game_over")
            await receive_type(ws, "round_end")

        fake_scheduler.reset()

        for ws in (host_game, g1_game, g2_game):
            await receive_type(ws, "session_over")
