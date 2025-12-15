import random
import uuid

import pytest

from backend.tests.multiplayer.ws_helpers import (
    drain_ws,
    random_cell,
    recv_round_ready,
    recv_until,
    ws_receive_json,
)
from backend.tests.utils.cookies import using_auth_cookie, using_auth_cookie_sync


@pytest.mark.anyio
async def test_multiplayer_single_player_flow(client, auth, ws_client, fake_scheduler):
    random.seed(0)

    host = await auth(
        email=f"mp-host-{uuid.uuid4().hex[:8]}@example.com",
        password="pw",
        nickname="mp_host",
    )
    host_cookie = host["auth_cookie"]

    async with using_auth_cookie(client, host_cookie):
        create_resp = await client.post("/api/lobbies")
        assert create_resp.status_code == 200
        lobby_id = create_resp.json()["id"]
        session_id = lobby_id

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

    with (
        using_auth_cookie_sync(ws_client, host_cookie),
        ws_client.websocket_connect("/api/ws") as notif_ws,
        ws_client.websocket_connect(f"/api/game/multi/{session_id}") as game_ws,
    ):
        game_ws.send_json({"type": "ready"})
        assert recv_until(notif_ws, {"user_ready"})["value"] is True

        recv_round_ready(notif_ws=notif_ws, game_ws=game_ws)
        recv_until(game_ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"lock_ready", "start_round"})
        start_msg = recv_until(game_ws, {"round_start"}, timeout_s=10.0)
        start_field = tuple(start_msg["start_field"])

        flagged = random_cell(rows=3, cols=3, exclude=start_field)
        game_ws.send_json({"type": "flag", "cell": [flagged[0], flagged[1]]})
        recv_until(game_ws, {"flag"}, timeout_s=5.0)

        drain_ws(game_ws)

        game_ws.send_json({"type": "reveal_one", "cell": [flagged[0], flagged[1]]})
        with pytest.raises(TimeoutError):
            ws_receive_json(game_ws, timeout_s=0.25)

        fake_scheduler.run_matching({"end_round"})
        recv_until(game_ws, {"round_end"}, timeout_s=10.0)

        game_ws.send_json({"type": "ready"})
        recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)

        game_ws.send_json({"type": "not_ready"})
        msg = recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)
        assert msg["value"] is False

        fake_scheduler.run_matching({"lock_ready", "start_round"})

        game_ws.send_json({"type": "ready"})
        recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)

        recv_until(game_ws, {"round_ready"}, timeout_s=10.0)
        recv_until(game_ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"lock_ready", "start_round"})
        recv_until(game_ws, {"round_start"}, timeout_s=10.0)

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        game_ws.send_json({"type": "flag", "cell": [cell[0], cell[1]]})
        recv_until(game_ws, {"flag"}, timeout_s=5.0)

        fake_scheduler.run_matching({"end_round"})
        recv_until(game_ws, {"round_end"}, timeout_s=10.0)

        game_ws.send_json({"type": "ready"})
        recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)

        recv_until(game_ws, {"round_ready"}, timeout_s=10.0)
        recv_until(game_ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"lock_ready", "start_round"})
        recv_until(game_ws, {"round_start"}, timeout_s=10.0)

        fake_scheduler.run_matching({"end_round"})
        recv_until(game_ws, {"round_end"}, timeout_s=10.0)
        recv_until(game_ws, {"session_over"}, timeout_s=10.0)
