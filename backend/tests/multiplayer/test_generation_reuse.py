import uuid
from contextlib import AsyncExitStack
from datetime import timedelta

import pytest

from backend.tests.multiplayer.ws_helpers import receive_type


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"p1-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"p1_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"p2-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"p2_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_generation_reuse(authenticated_clients, fake_scheduler):
    p1_bundle = authenticated_clients[0]
    p2_bundle = authenticated_clients[1]

    difficulty = {"rows": 16, "columns": 30, "mine_count": 99}

    create_resp = await p1_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id_1 = create_resp.json()["id"]

    update_resp = await p1_bundle.http.put(
        f"/lobbies/{lobby_id_1}",
        json={
            "rounds": 1,
            "max_round_time": 60,
            "difficulty_level": difficulty,
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert update_resp.status_code == 200

    async with AsyncExitStack() as stack:
        p1_ws = await stack.enter_async_context(
            p1_bundle.ws(f"/game/multi/{lobby_id_1}")
        )
        await receive_type(p1_ws, "session_state")
        await receive_type(p1_ws, "user_ready")

        await p1_ws.send_json({"type": "ready"})

        await receive_type(p1_ws, "user_ready")
        await receive_type(p1_ws, "round_ready")
        await receive_type(p1_ws, "round_countdown")
        await fake_scheduler.skip(timedelta(seconds=10))
        await receive_type(p1_ws, "round_start")

        await fake_scheduler.skip(timedelta=timedelta(seconds=60))
        msg = await receive_type(p1_ws, "game_over")
        minefields_1 = msg["full_board"]

        await receive_type(p1_ws, "round_end")
        await receive_type(p1_ws, "session_over")

    create_resp = await p2_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id_2 = create_resp.json()["id"]

    update_resp = await p2_bundle.http.put(
        f"/lobbies/{lobby_id_2}",
        json={
            "rounds": 1,
            "max_round_time": 60,
            "difficulty_level": difficulty,
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert update_resp.status_code == 200

    async with AsyncExitStack() as stack:
        p2_ws = await stack.enter_async_context(
            p2_bundle.ws(f"/game/multi/{lobby_id_2}")
        )
        await receive_type(p2_ws, "session_state")
        await receive_type(p2_ws, "user_ready")

        await p2_ws.send_json({"type": "ready"})

        await receive_type(p2_ws, "user_ready")
        await receive_type(p2_ws, "round_ready")
        await receive_type(p2_ws, "round_countdown")
        await fake_scheduler.skip(timedelta(seconds=10))
        await receive_type(p2_ws, "round_start")

        await fake_scheduler.skip(timedelta=timedelta(seconds=60))
        msg = await receive_type(p2_ws, "game_over")
        minefields_2 = msg["full_board"]

        await receive_type(p2_ws, "round_end")
        await receive_type(p2_ws, "session_over")

    assert minefields_1 == minefields_2, "Boards should be identical"
