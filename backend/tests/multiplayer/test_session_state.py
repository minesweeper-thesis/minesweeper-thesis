from contextlib import AsyncExitStack
from datetime import timedelta

import pytest

from backend.tests.conftest import AuthenticatedClientBundle
from backend.tests.multiplayer.ws_helpers import receive_type


@pytest.mark.asyncio(loop_scope="session")
async def test_session_state_flow(
    authenticated_clients: list[AuthenticatedClientBundle], fake_scheduler
):
    host_bundle = authenticated_clients[0]

    create_resp = await host_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]

    update_resp = await host_bundle.http.put(
        f"/lobbies/{lobby_id}",
        json={
            "rounds": 2,
            "max_round_time": 60,
            "difficulty_level": {"rows": 16, "columns": 16, "mine_count": 40},
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert update_resp.status_code == 200

    async with AsyncExitStack() as stack:
        lobby_ws = await stack.enter_async_context(
            host_bundle.ws(f"/game/multi/{lobby_id}")
        )

        state = await receive_type(lobby_ws, "session_state")
        assert state["round"]["state"] == "not_ready"
        assert state["round"]["round_number"] == 1

        await receive_type(lobby_ws, "user_ready")

        await lobby_ws.send_json({"type": "ready"})
        await receive_type(lobby_ws, "user_ready")

        await receive_type(lobby_ws, "round_ready")
        await receive_type(lobby_ws, "round_countdown")

        await lobby_ws.send_json({"type": "get_session_state"})
        state = await receive_type(lobby_ws, "session_state")
        assert state["round"]["state"] == "countdown"
        assert state["round"]["countdown_to"] is not None

        await fake_scheduler.skip(timedelta(seconds=6))

        await lobby_ws.send_json({"type": "get_session_state"})
        state = await receive_type(lobby_ws, "session_state")
        assert state["round"]["state"] == "ready_lock"
        assert state["round"]["start_at"] is not None

        await fake_scheduler.skip(timedelta(seconds=5))

        start_msg = await receive_type(lobby_ws, "round_start")
        start_field = tuple(start_msg["start_field"])

        await lobby_ws.send_json({"type": "get_session_state"})
        state = await receive_type(lobby_ws, "session_state")
        assert state["round"]["state"] == "playing"
        assert state["round"]["start_at"] is not None
        assert state["round"]["end_at"] is not None

        await lobby_ws.send_json(
            {"type": "reveal_one", "cell": [start_field[0], start_field[1]]}
        )

        await receive_type(lobby_ws, "reveal")
        await receive_type(lobby_ws, "score_update")

        await lobby_ws.send_json({"type": "get_session_state"})
        state = await receive_type(lobby_ws, "session_state")
        scoreboard = state["scoreboard"]
        user_score_item = next(
            item for item in scoreboard if item["user_id"] == str(host_bundle.user_id)
        )

        assert "score" in user_score_item

        await fake_scheduler.skip(timedelta(seconds=60))
        await receive_type(lobby_ws, "game_over")
        await receive_type(lobby_ws, "round_end")

        await lobby_ws.send_json({"type": "get_session_state"})
        state = await receive_type(lobby_ws, "session_state")

        assert state["round"]["state"] == "not_ready"
        assert state["round"]["round_number"] == 2
