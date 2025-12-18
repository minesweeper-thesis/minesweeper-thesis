import random

import pytest

from backend.tests.conftest import AuthenticatedClientBundle
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
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_multiplayer_single_player_flow(
    authenticated_clients: list[AuthenticatedClientBundle],
    fake_scheduler,
    background_handler_override,
):
    random.seed(0)

    host_bundle = authenticated_clients[0]

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

    from contextlib import ExitStack

    with ExitStack() as stack:
        notif_ws = stack.enter_context(host_bundle.get_ws())
        game_ws = stack.enter_context(host_bundle.get_ws_multi_game(session_id))
        game_ws.send_json({"type": "ready"})
        assert recv_until(notif_ws, {"user_ready"})["value"] is True

        recv_round_ready(notif_ws=notif_ws, game_ws=game_ws)
        recv_until(game_ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})
        start_msg = recv_until(game_ws, {"round_start"}, timeout_s=10.0)
        start_field = tuple(start_msg["start_field"])

        flagged = random_cell(rows=3, cols=3, exclude=start_field)
        game_ws.send_json({"type": "flag", "cell": [flagged[0], flagged[1]]})
        recv_until(game_ws, {"flag"}, timeout_s=5.0)

        drain_ws(game_ws)

        game_ws.send_json({"type": "reveal_one", "cell": [flagged[0], flagged[1]]})
        with pytest.raises(TimeoutError):
            ws_receive_json(game_ws, timeout_s=0.25)

        fake_scheduler.run_matching({"_end_round"})
        recv_until(game_ws, {"round_end"}, timeout_s=10.0)

        game_ws.send_json({"type": "ready"})
        recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)

        game_ws.send_json({"type": "not_ready"})
        msg = recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)
        assert msg["value"] is False

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})

        game_ws.send_json({"type": "ready"})
        recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)

        recv_until(game_ws, {"round_ready"}, timeout_s=10.0)
        recv_until(game_ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})
        recv_until(game_ws, {"round_start"}, timeout_s=10.0)

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        game_ws.send_json({"type": "flag", "cell": [cell[0], cell[1]]})
        recv_until(game_ws, {"flag"}, timeout_s=5.0)

        fake_scheduler.run_matching({"_end_round"})
        recv_until(game_ws, {"round_end"}, timeout_s=10.0)

        game_ws.send_json({"type": "ready"})
        recv_until(notif_ws, {"user_ready"}, timeout_s=5.0)

        recv_until(game_ws, {"round_ready"}, timeout_s=10.0)
        recv_until(game_ws, {"round_countdown"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        fake_scheduler.run_matching({"start_round"})
        recv_until(game_ws, {"round_start"}, timeout_s=10.0)

        fake_scheduler.run_matching({"_end_round"})
        recv_until(game_ws, {"round_end"}, timeout_s=10.0)
        recv_until(game_ws, {"session_over"}, timeout_s=10.0)
