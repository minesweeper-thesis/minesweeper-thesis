import random
import uuid
from contextlib import AsyncExitStack

import pytest

from backend.tests.multiplayer.ws_helpers import (
    drain_ws,
    random_cell,
    recv_round_ready,
    recv_until,
    ws_receive_json,
)


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

        assert (await host_notif.receive_json())["type"] == "current_lobby"
        assert (await g1_notif.receive_json())["type"] == "current_lobby"
        assert (await g2_notif.receive_json())["type"] == "current_lobby"

        assert (
            await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations",
                json={"user_id": g1_id},
            )
        ).status_code in [200, 204]
        inv1 = await recv_until(g1_notif, {"invitation"})
        assert (
            await g1_bundle.http.post(
                f"/lobbies/{lobby_id}/join",
                json={"invitation_id": inv1["id"]},
            )
        ).status_code == 200

        assert (
            await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations",
                json={"user_id": g2_id},
            )
        ).status_code in [200, 204]
        inv2 = await recv_until(g2_notif, {"invitation"})
        assert (
            await g2_bundle.http.post(
                f"/lobbies/{lobby_id}/join",
                json={"invitation_id": inv2["id"]},
            )
        ).status_code == 200

        host_game = await stack.enter_async_context(
            host_bundle.ws(f"/game/multi/{session_id}")
        )
        g1_game = await stack.enter_async_context(
            g1_bundle.ws(f"/game/multi/{session_id}")
        )
        g2_game = await stack.enter_async_context(
            g2_bundle.ws(f"/game/multi/{session_id}")
        )

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is True

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is True

        await g2_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is True

        await recv_round_ready(notif_ws=host_notif, game_ws=host_game)
        await recv_round_ready(notif_ws=g1_notif, game_ws=g1_game)
        await recv_round_ready(notif_ws=g2_notif, game_ws=g2_game)

        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await g1_game.send_json({"type": "not_ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is False

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is True

        await recv_round_ready(notif_ws=host_notif, game_ws=host_game)
        await recv_round_ready(notif_ws=g1_notif, game_ws=g1_game)
        await recv_round_ready(notif_ws=g2_notif, game_ws=g2_game)
        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})

        starts = [
            await recv_until(ws, {"round_start"})
            for ws in (host_game, g1_game, g2_game)
        ]
        start_field = tuple(starts[0]["start_field"])

        invalid_cell = random_cell(rows=3, cols=3, exclude=start_field)
        await host_game.send_json(
            {"type": "flag", "cell": [invalid_cell[0], invalid_cell[1]]}
        )
        await recv_until(host_game, {"flag"}, timeout_s=5.0)

        await drain_ws(host_game)

        await host_game.send_json(
            {"type": "reveal_one", "cell": [invalid_cell[0], invalid_cell[1]]}
        )
        with pytest.raises(TimeoutError):
            await ws_receive_json(host_game, timeout_s=0.25)

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        await g1_game.send_json({"type": "reveal_one", "cell": [cell[0], cell[1]]})
        await recv_until(
            g1_game, {"reveal", "game_over", "score_update"}, timeout_s=5.0
        )

        await fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_end"}, timeout_s=10.0)

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            await recv_until(ws, {"user_ready"})

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            await recv_until(ws, {"user_ready"})

        await g1_game.send_json({"type": "not_ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            msg = await recv_until(ws, {"user_ready"})
            assert msg["value"] is False

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})

        await g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            await recv_until(ws, {"user_ready"})

        await g2_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            await recv_until(ws, {"user_ready"})

        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_ready"}, timeout_s=10.0)
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})
        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_start"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            cell = random_cell(rows=3, cols=3, exclude=start_field)
            await ws.send_json({"type": "reveal_one", "cell": [cell[0], cell[1]]})
            await recv_until(ws, {"reveal", "game_over", "score_update"}, timeout_s=5.0)

        await fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_end"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            await ws.send_json({"type": "ready"})
        for _ in range(3):
            for ws in (host_notif, g1_notif, g2_notif):
                await recv_until(ws, {"user_ready"})

        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_ready"}, timeout_s=10.0)
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})
        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_start"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"round_end"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            await recv_until(ws, {"session_over"}, timeout_s=10.0)
