import random
import uuid
from contextlib import AsyncExitStack
from datetime import datetime, timedelta

import pytest

from backend.tests.conftest import AuthenticatedClientBundle
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
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_multiplayer_single_player_flow(
    authenticated_clients: list[AuthenticatedClientBundle], fake_scheduler
):
    random.seed(0)

    host_bundle = authenticated_clients[0]

    create_resp = await host_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]

    update_resp = await host_bundle.http.put(
        f"/lobbies/{lobby_id}",
        json={
            "rounds": 3,
            "max_round_time": 60,
            "difficulty_level": {"rows": 3, "columns": 3, "mine_count": 3},
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert update_resp.status_code == 200

    async with AsyncExitStack() as stack:
        notif_ws = await stack.enter_async_context(host_bundle.ws())

        msg = await receive_type(notif_ws, "current_lobby")

        lobby_ws = await stack.enter_async_context(
            host_bundle.ws(f"/game/multi/{lobby_id}")
        )

        await receive_type(lobby_ws, "session_state")
        await receive_type(lobby_ws, "user_ready")

        await lobby_ws.send_json({"type": "ready"})
        msg = await receive_type(lobby_ws, "user_ready")
        assert msg["value"] is True, f"received {msg}"

        msg = await receive_type(lobby_ws, "round_ready")

        await receive_type(lobby_ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))

        start_msg = await receive_type(lobby_ws, "round_start")
        start_field = tuple(start_msg["start_field"])

        flagged = random_cell(rows=3, cols=3, exclude=start_field)
        await lobby_ws.send_json({"type": "flag", "cell": [flagged[0], flagged[1]]})
        msg = await receive_type(lobby_ws, "flag")

        await lobby_ws.send_json(
            {"type": "remove_flag", "cell": [flagged[0], flagged[1]]}
        )
        msg = await receive_type(lobby_ws, "remove_flag")

        await fake_scheduler.skip(timedelta(seconds=60))
        await receive_type(lobby_ws, "game_over")
        await receive_type(lobby_ws, "score_update")
        msg = await receive_type(lobby_ws, "round_end")
        assert msg["type"] == "round_end"

        await lobby_ws.send_json({"type": "ready"})
        msg = await receive_type(lobby_ws, "user_ready")
        assert msg["type"] == "user_ready"
        assert msg["value"] is True

        await receive_type(lobby_ws, "round_ready")
        await receive_type(lobby_ws, "round_countdown")

        await lobby_ws.send_json({"type": "not_ready"})
        msg = await receive_type(lobby_ws, "user_ready")
        assert msg["value"] is False

        await lobby_ws.send_json({"type": "ready"})
        msg = await receive_type(lobby_ws, "user_ready")
        assert msg["value"] is True

        await receive_type(lobby_ws, "round_ready")
        await receive_type(lobby_ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        msg = await receive_type(lobby_ws, "round_start")
        assert msg["type"] == "round_start"

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        await lobby_ws.send_json({"type": "flag", "cell": [cell[0], cell[1]]})
        await receive_type(lobby_ws, "flag")

        await fake_scheduler.skip(timedelta(seconds=60))
        await receive_type(lobby_ws, "game_over")
        await receive_type(lobby_ws, "score_update")
        msg = await receive_type(lobby_ws, "round_end")
        assert msg["type"] == "round_end"

        await lobby_ws.send_json({"type": "ready"})
        await receive_type(lobby_ws, "user_ready")

        await receive_type(lobby_ws, "round_ready")
        await receive_type(lobby_ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))
        await receive_type(lobby_ws, "round_start")

        await fake_scheduler.skip(timedelta(seconds=60))
        await receive_type(lobby_ws, "game_over")
        await receive_type(lobby_ws, "score_update")
        await receive_type(lobby_ws, "round_end")
        await receive_type(lobby_ws, "session_over")
