import random
from contextlib import AsyncExitStack

import pytest

from backend.tests.multiplayer.ws_helpers import (
    drain_ws,
    random_cell,
    recv_round_ready,
    recv_until,
    recv_until_all,
    ws_receive_json,
)


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {"email": "mp-host@example.com", "password": "pw", "nickname": "mp_host"},
            {"email": "mp-guest@example.com", "password": "pw", "nickname": "mp_guest"},
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_multiplayer_two_player_flow(
    authenticated_clients, fake_scheduler, background_handler_override
):
    random.seed(0)

    host_bundle = authenticated_clients[0]
    guest_bundle = authenticated_clients[1]

    guest_id = guest_bundle.user_id

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

    async with AsyncExitStack() as stack:
        host_notif = await stack.enter_async_context(host_bundle.ws())
        guest_notif = await stack.enter_async_context(guest_bundle.ws())
        assert (await host_notif.receive_json())["type"] == "current_lobby"
        assert (await guest_notif.receive_json())["type"] == "current_lobby"

        inv_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/invitations",
            json={"user_id": guest_id},
        )
        assert inv_resp.status_code in [200, 204]

        invitation = await recv_until(guest_notif, {"invitation"})
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

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is True

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is True

        await recv_round_ready(notif_ws=host_notif, game_ws=host_game)
        await recv_round_ready(notif_ws=guest_notif, game_ws=guest_game)
        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await guest_game.send_json({"type": "not_ready"})
        for ws in (host_notif, guest_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is False

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            assert (await recv_until(ws, {"user_ready"}))["value"] is True

        await recv_round_ready(notif_ws=host_notif, game_ws=host_game)
        await recv_round_ready(notif_ws=guest_notif, game_ws=guest_game)
        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})
        start_host = await recv_until(host_game, {"round_start"}, timeout_s=10.0)
        await recv_until(guest_game, {"round_start"}, timeout_s=10.0)
        start_field = tuple(start_host["start_field"])

        flagged = random_cell(rows=3, cols=3, exclude=start_field)
        await host_game.send_json({"type": "flag", "cell": [flagged[0], flagged[1]]})
        await recv_until(host_game, {"flag"}, timeout_s=5.0)

        await drain_ws(host_game)

        await host_game.send_json(
            {"type": "reveal_one", "cell": [flagged[0], flagged[1]]}
        )
        with pytest.raises(TimeoutError):
            await ws_receive_json(host_game, timeout_s=0.25)

        await fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_end"}, timeout_s=10.0)

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await recv_until(ws, {"user_ready"}, timeout_s=5.0)

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await recv_until(ws, {"user_ready"}, timeout_s=5.0)

        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_ready"}, timeout_s=10.0)
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await host_game.send_json({"type": "not_ready"})
        for ws in (host_notif, guest_notif):
            msg = await recv_until(ws, {"user_ready"}, timeout_s=5.0)
            assert msg["value"] is False

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await recv_until(ws, {"user_ready"}, timeout_s=5.0)

        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_ready"}, timeout_s=10.0)
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})
        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_start"}, timeout_s=10.0)

        cell = random_cell(rows=3, cols=3, exclude=start_field)
        await guest_game.send_json({"type": "flag", "cell": [cell[0], cell[1]]})
        await recv_until(guest_game, {"flag"}, timeout_s=5.0)

        await fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_end"}, timeout_s=10.0)

        await host_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await recv_until(ws, {"user_ready"}, timeout_s=5.0)

        await guest_game.send_json({"type": "ready"})
        for ws in (host_notif, guest_notif):
            await recv_until(ws, {"user_ready"}, timeout_s=5.0)

        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_ready"}, timeout_s=10.0)
            await recv_until(ws, {"round_countdown"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_lock_ready_and_schedule_start"})
        await fake_scheduler.run_matching({"start_round"})
        for ws in (host_game, guest_game):
            await recv_until(ws, {"round_start"}, timeout_s=10.0)

        await fake_scheduler.run_matching({"_end_round"})
        for ws in (host_game, guest_game):
            await recv_until_all(ws, {"round_end", "session_over"}, timeout_s=10.0)
