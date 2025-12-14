import json
import random
import uuid
from contextlib import ExitStack

import pytest

from backend.repositories.multiplayer_repo import sessions
from backend.tests.multiplayer.ws_helpers import (
    drain_ws,
    random_cell,
    recv_round_ready,
    recv_until,
    ws_receive_json,
)
from backend.tests.utils.cookies import using_auth_cookie, using_auth_cookie_sync


@pytest.mark.anyio
async def test_multiplayer_full_flow_many_players(
    client, auth, fake_scheduler, ws_client
):
    random.seed(0)

    host_email = f"mp-host-{uuid.uuid4().hex[:8]}@example.com"
    host = await auth(email=host_email, password="pw", nickname="mp_host")
    host_cookie = host["auth_cookie"]

    async with using_auth_cookie(client, host_cookie):
        create_resp = await client.post("/api/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]
    session_id = lobby_id

    async with using_auth_cookie(client, host_cookie):
        update_resp = await client.put(
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

    guest1_email = f"mp-g1-{uuid.uuid4().hex[:8]}@example.com"
    guest2_email = f"mp-g2-{uuid.uuid4().hex[:8]}@example.com"

    g1 = await auth(email=guest1_email, password="pw", nickname="mp_g1")
    g2 = await auth(email=guest2_email, password="pw", nickname="mp_g2")

    g1_cookie = g1["auth_cookie"]
    g2_cookie = g2["auth_cookie"]
    g1_id = g1["user_id"]
    g2_id = g2["user_id"]

    with ExitStack() as stack:
        with using_auth_cookie_sync(ws_client, host_cookie):
            host_notif = stack.enter_context(ws_client.websocket_connect("/api/ws"))
        with using_auth_cookie_sync(ws_client, g1_cookie):
            g1_notif = stack.enter_context(ws_client.websocket_connect("/api/ws"))
        with using_auth_cookie_sync(ws_client, g2_cookie):
            g2_notif = stack.enter_context(ws_client.websocket_connect("/api/ws"))

        assert json.loads(host_notif.receive_text())["type"] == "current_lobby"
        assert json.loads(g1_notif.receive_text())["type"] == "current_lobby"
        assert json.loads(g2_notif.receive_text())["type"] == "current_lobby"

        async with using_auth_cookie(client, host_cookie):
            assert (
                await client.post(
                    f"/api/lobbies/{lobby_id}/invitations",
                    json={"user_id": g1_id},
                )
            ).status_code in [200, 204]
        inv1 = recv_until(g1_notif, {"invitation"})
        async with using_auth_cookie(client, g1_cookie):
            assert (
                await client.post(
                    f"/api/lobbies/{lobby_id}/join",
                    json={"invitation_id": inv1["id"]},
                )
            ).status_code == 200

        async with using_auth_cookie(client, host_cookie):
            assert (
                await client.post(
                    f"/api/lobbies/{lobby_id}/invitations",
                    json={"user_id": g2_id},
                )
            ).status_code in [200, 204]
        inv2 = recv_until(g2_notif, {"invitation"})
        async with using_auth_cookie(client, g2_cookie):
            assert (
                await client.post(
                    f"/api/lobbies/{lobby_id}/join",
                    json={"invitation_id": inv2["id"]},
                )
            ).status_code == 200

        with using_auth_cookie_sync(ws_client, host_cookie):
            host_game = stack.enter_context(
                ws_client.websocket_connect(f"/api/game/multi/{session_id}")
            )
        with using_auth_cookie_sync(ws_client, g1_cookie):
            g1_game = stack.enter_context(
                ws_client.websocket_connect(f"/api/game/multi/{session_id}")
            )
        with using_auth_cookie_sync(ws_client, g2_cookie):
            g2_game = stack.enter_context(
                ws_client.websocket_connect(f"/api/game/multi/{session_id}")
            )

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

        fake_scheduler.run_matching({"lock_ready", "start_round"})
        assert sessions[uuid.UUID(session_id)].current_round_index == -1

        g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            assert recv_until(ws, {"user_ready"})["value"] is True

        recv_round_ready(notif_ws=host_notif, game_ws=host_game)
        recv_round_ready(notif_ws=g1_notif, game_ws=g1_game)
        recv_round_ready(notif_ws=g2_notif, game_ws=g2_game)
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"lock_ready", "start_round"})

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

        fake_scheduler.run_matching({"end_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_end"}, timeout_s=10.0)
        assert sessions[uuid.UUID(session_id)].current_round_index == 0

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

        fake_scheduler.run_matching({"lock_ready", "start_round"})
        assert sessions[uuid.UUID(session_id)].current_round_index == 0

        g1_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            recv_until(ws, {"user_ready"})

        g2_game.send_json({"type": "ready"})
        for ws in (host_notif, g1_notif, g2_notif):
            recv_until(ws, {"user_ready"})

        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_ready"}, timeout_s=10.0)
            recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"lock_ready", "start_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_start"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            cell = random_cell(rows=3, cols=3, exclude=start_field)
            ws.send_json({"type": "reveal_one", "cell": [cell[0], cell[1]]})
            recv_until(ws, {"reveal", "game_over", "score_update"}, timeout_s=5.0)

        fake_scheduler.run_matching({"end_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_end"}, timeout_s=10.0)
        assert sessions[uuid.UUID(session_id)].current_round_index == 1

        for ws in (host_game, g1_game, g2_game):
            ws.send_json({"type": "ready"})
        for _ in range(3):
            for ws in (host_notif, g1_notif, g2_notif):
                recv_until(ws, {"user_ready"})

        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_ready"}, timeout_s=10.0)
            recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"lock_ready", "start_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_start"}, timeout_s=10.0)

        fake_scheduler.run_matching({"end_round"})
        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"round_end"}, timeout_s=10.0)

        for ws in (host_game, g1_game, g2_game):
            recv_until(ws, {"session_over"}, timeout_s=10.0)
