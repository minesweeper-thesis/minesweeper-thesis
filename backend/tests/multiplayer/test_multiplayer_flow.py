import json
import random
from contextlib import ExitStack

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
            {"email": "mp-host@example.com", "password": "pw", "nickname": "mp_host"},
            {"email": "mp-g1@example.com", "password": "pw", "nickname": "mp_g1"},
            {"email": "mp-g2@example.com", "password": "pw", "nickname": "mp_g2"},
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_multiplayer_full_flow_many_players(
    authenticated_clients, fake_scheduler, background_handler_override
):
    random.seed(0)

    host_bundle = authenticated_clients[0]
    g1_bundle = authenticated_clients[1]
    g2_bundle = authenticated_clients[2]

    create_resp = await host_bundle.http.post("/api/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]
    session_id = lobby_id

    update_resp = await host_bundle.http.put(
        f"/api/lobbies/{lobby_id}",
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

    with ExitStack() as stack:
        host_notif = stack.enter_context(host_bundle.get_ws())
        g1_notif = stack.enter_context(g1_bundle.get_ws())
        g2_notif = stack.enter_context(g2_bundle.get_ws())

        assert json.loads(host_notif.receive_text())["type"] == "current_lobby"
        assert json.loads(g1_notif.receive_text())["type"] == "current_lobby"
        assert json.loads(g2_notif.receive_text())["type"] == "current_lobby"

        assert (
            await host_bundle.http.post(
                f"/api/lobbies/{lobby_id}/invitations",
                json={"user_id": g1_id},
            )
        ).status_code in [200, 204]
        inv1 = recv_until(g1_notif, {"invitation"})
        assert (
            await g1_bundle.http.post(
                f"/api/lobbies/{lobby_id}/join",
                json={"invitation_id": inv1["id"]},
            )
        ).status_code == 200

        assert (
            await host_bundle.http.post(
                f"/api/lobbies/{lobby_id}/invitations",
                json={"user_id": g2_id},
            )
        ).status_code in [200, 204]
        inv2 = recv_until(g2_notif, {"invitation"})
        assert (
            await g2_bundle.http.post(
                f"/api/lobbies/{lobby_id}/join",
                json={"invitation_id": inv2["id"]},
            )
        ).status_code == 200

        host_game = stack.enter_context(host_bundle.get_ws_multi_game(session_id))
        g1_game = stack.enter_context(g1_bundle.get_ws_multi_game(session_id))
        g2_game = stack.enter_context(g2_bundle.get_ws_multi_game(session_id))

        host_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert recv_until(ws, {"user_ready"})["value"] is True

        g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert recv_until(ws, {"user_ready"})["value"] is True

        g2_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert recv_until(ws, {"user_ready"})["value"] is True

        recv_round_ready(notif_ws=host_notif, game_ws=host_game)
        recv_round_ready(notif_ws=g1_notif, game_ws=g1_game)
        recv_round_ready(notif_ws=g2_notif, game_ws=g2_game)

        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        g1_game.send_json({"type": "not_ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert recv_until(ws, {"user_ready"})["value"] is False

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})

        g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert recv_until(ws, {"user_ready"})["value"] is True

        recv_round_ready(notif_ws=host_notif, game_ws=host_game)
        recv_round_ready(notif_ws=g1_notif, game_ws=g1_game)
        recv_round_ready(notif_ws=g2_notif, game_ws=g2_game)
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})

        starts = [
            recv_until(ws, {"round_start"}) for ws in (host_game, g1_game, g2_game)
        ]
        start_field = tuple(starts[0]["start_field"])

        invalid_cell = random_cell(rows=3, cols=3, exclude=start_field)
        host_game.send_json(
            {"type": "flag", "cell": [invalid_cell[0], invalid_cell[1]]}
        )
        recv_until(host_game, {"flag"}, timeout_s=5.0)

        drain_ws(host_game)

        host_game.send_json(
            {"type": "reveal_one", "cell": [invalid_cell[0], invalid_cell[1]]}
        )
        with pytest.raises(TimeoutError):
            ws_receive_json(host_game, timeout_s=0.25)

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        g1_game.send_json({"type": "reveal_one", "cell": [cell[0], cell[1]]})
        recv_until(g1_game, {"reveal", "game_over", "score_update"}, timeout_s=5.0)

        fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_end"}, timeout_s=10.0)

        host_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            recv_until(ws, {"user_ready"})

        g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            recv_until(ws, {"user_ready"})

        g1_game.send_json({"type": "not_ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            msg = recv_until(ws, {"user_ready"})
            assert msg["value"] is False

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})

        g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            recv_until(ws, {"user_ready"})

        g2_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            recv_until(ws, {"user_ready"})

        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_ready"}, timeout_s=10.0)
            recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_start"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            cell = random_cell(rows=3, cols=3, exclude=start_field)
            ws.send_json({"type": "reveal_one", "cell": [cell[0], cell[1]]})
            recv_until(ws, {"reveal", "game_over", "score_update"}, timeout_s=5.0)

        fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_end"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            ws.send_json({"type": "ready"})
        for _ in range(3):
            for ws in (host_notif, g1_notif, g2_notif):
                recv_until(ws, {"user_ready"})

        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_ready"}, timeout_s=10.0)
            recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_start"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_end"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"session_over"}, timeout_s=10.0)
