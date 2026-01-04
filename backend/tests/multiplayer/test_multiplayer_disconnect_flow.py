import asyncio
import random
import uuid
from contextlib import AsyncExitStack
from datetime import datetime, timedelta

import pytest

from backend.services.user import user_connection_service
from backend.tests.conftest import AuthenticatedClientBundle
from backend.tests.multiplayer.ws_helpers import receive_type


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
                "email": f"mp-guest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"mp_guest_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_multiplayer_disconnect_flow(
    authenticated_clients: list[AuthenticatedClientBundle],
):
    backup_delay = user_connection_service.REMOVE_OFFLINE_USER_DELAY
    try:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = timedelta(seconds=2)

        random.seed(0)

        host_bundle = authenticated_clients[0]
        guest_bundle = authenticated_clients[1]

        guest_id = guest_bundle.user_id

        create_resp = await host_bundle.http.post("/lobbies")
        assert create_resp.status_code == 200
        lobby_id = create_resp.json()["id"]

        async with AsyncExitStack() as stack:
            host_notif = await stack.enter_async_context(host_bundle.ws())
            guest_notif = await stack.enter_async_context(guest_bundle.ws())
            await receive_type(host_notif, "current_lobby")

            host_lobby = await stack.enter_async_context(
                host_bundle.ws(f"/game/multi/{lobby_id}")
            )
            await receive_type(host_lobby, "session_state")
            await receive_type(host_lobby, "user_ready")

            await receive_type(guest_notif, "current_lobby")

            inv_resp = await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations",
                json={"user_id": guest_id},
            )
            assert inv_resp.status_code == 200

            invitation = await receive_type(guest_notif, "invitation")

            guest_lobby = await stack.enter_async_context(
                guest_bundle.ws(
                    f"/game/multi/{lobby_id}?invitation_id={invitation['id']}"
                )
            )

            await receive_type(guest_lobby, "session_state")
            await receive_type(host_lobby, "invitation_response")
            await receive_type(guest_lobby, "user_ready")
            await receive_type(guest_lobby, "user_ready")
            await receive_type(host_lobby, "user_connection_status")

            await guest_lobby.send_json({"type": "ready"})

            msg = await receive_type(host_lobby, "user_ready")
            assert msg["user_id"] == str(guest_id)
            assert msg["value"] is True
            await receive_type(guest_lobby, "user_ready")

            await guest_notif.close()

            msg = await receive_type(host_lobby, "user_ready")
            assert msg["user_id"] == str(guest_id)
            assert msg["value"] is False

            msg = await receive_type(host_lobby, "user_online_status")
            assert msg["user"]["id"] == str(guest_id)
            assert msg["user"]["is_online"] is False

            msg = await receive_type(host_lobby, "user_connection_status")
            assert msg["user"]["id"] == str(guest_id)
            assert msg["status"] == "disconnected"
    finally:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = backup_delay


@pytest.mark.time_machine(datetime.now())
@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"offline-host-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"offline_host_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"offline-g1-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"offline_g1_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_lobby_ws_reconnect(
    authenticated_clients: list[AuthenticatedClientBundle], fake_scheduler
):
    random.seed(0)

    host_bundle = authenticated_clients[0]
    g1_bundle = authenticated_clients[1]

    g1_id = g1_bundle.user_id

    create_resp = await host_bundle.http.post("/lobbies")
    assert create_resp.status_code == 200
    lobby_id = create_resp.json()["id"]

    update_resp = await host_bundle.http.put(
        f"/lobbies/{lobby_id}",
        json={
            "rounds": 1,
            "max_round_time": 60,
            "difficulty_level": {"rows": 3, "columns": 3, "mine_count": 1},
            "game_mode": "normal",
            "generator": {"type": "random", "settings": None},
        },
    )
    assert update_resp.status_code in [200, 204]

    async with AsyncExitStack() as stack:
        host_notif = await stack.enter_async_context(host_bundle.ws())
        await receive_type(host_notif, "current_lobby")

        host_lobby = await stack.enter_async_context(
            host_bundle.ws(f"/game/multi/{lobby_id}")
        )
        await receive_type(host_lobby, "session_state")
        await receive_type(host_lobby, "user_ready")

        g1_notif = await stack.enter_async_context(g1_bundle.ws())
        await receive_type(g1_notif, "current_lobby")

        inv1_resp = await host_bundle.http.post(
            f"/lobbies/{lobby_id}/invitations", json={"user_id": g1_id}
        )
        assert inv1_resp.status_code == 200
        invitation1 = await receive_type(g1_notif, "invitation")

        g1_lobby = await stack.enter_async_context(
            g1_bundle.ws(f"/game/multi/{lobby_id}?invitation_id={invitation1['id']}")
        )
        await receive_type(g1_lobby, "session_state")
        await receive_type(g1_lobby, "user_ready")
        await receive_type(g1_lobby, "user_ready")

        await receive_type(host_lobby, "invitation_response")
        await receive_type(host_lobby, "user_connection_status")

        await host_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, g1_lobby):
            await receive_type(ws, "user_ready")

        await g1_lobby.send_json({"type": "ready"})
        for ws in (host_lobby, g1_lobby):
            await receive_type(ws, "user_ready")

        for ws in (host_lobby, g1_lobby):
            await receive_type(ws, "round_ready")

        for ws in (host_lobby, g1_lobby):
            await receive_type(ws, "round_countdown")

        await fake_scheduler.skip(timedelta(seconds=10))

        for ws in (host_lobby, g1_lobby):
            start_msg = await receive_type(ws, "round_start")
            start_field = start_msg["start_field"]

        await g1_notif.close()
        await g1_lobby.close()

        msg = await receive_type(host_lobby, "user_online_status")
        assert msg["user"]["id"] == str(g1_id)
        assert msg["user"]["is_online"] is False

        for i, j in [(i, j) for i in range(3) for j in range(3)]:
            await host_lobby.send_json({"type": "reveal_one", "cell": [i, j]})
            msg = await receive_type(host_lobby, "reveal")

            await receive_type(host_lobby, "score_update")
            if msg["game_status"] == "finished":
                await receive_type(host_lobby, "game_over")
                break

        g1_notif = await stack.enter_async_context(g1_bundle.ws())
        await receive_type(g1_notif, "current_lobby")

        g1_lobby = await stack.enter_async_context(
            g1_bundle.ws(f"/game/multi/{lobby_id}")
        )
        await receive_type(g1_lobby, "session_state")
        await receive_type(g1_lobby, "user_ready")
        await receive_type(g1_lobby, "user_ready")

        msg = await receive_type(host_lobby, "user_online_status")
        assert msg["user"]["id"] == str(g1_id)
        assert msg["user"]["is_online"] is True

        await g1_lobby.send_json({"type": "reveal_one", "cell": start_field})
        await receive_type(g1_lobby, "reveal")
        for ws in (host_lobby, g1_lobby):
            await receive_type(ws, "score_update")

        await fake_scheduler.skip(timedelta(seconds=60))

        await receive_type(g1_lobby, "game_over")

        for ws in (host_lobby, g1_lobby):
            await receive_type(ws, "score_update")

        for ws in (host_lobby, g1_lobby):
            await receive_type(ws, "round_end")

        await receive_type(host_lobby, "session_over")
        await receive_type(g1_lobby, "session_over")


@pytest.mark.time_machine(datetime.now())
@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"offline-host-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"offline_host_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"offline-g1-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"offline_g1_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"offline-g2-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"offline_g2_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_flow_with_disconnected_user(
    authenticated_clients: list[AuthenticatedClientBundle], fake_scheduler
):
    backup_delay = user_connection_service.REMOVE_OFFLINE_USER_DELAY
    try:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = timedelta(seconds=1.5)

        random.seed(0)

        host_bundle = authenticated_clients[0]
        g1_bundle = authenticated_clients[1]
        g2_bundle = authenticated_clients[2]

        g1_id = g1_bundle.user_id
        g2_id = g2_bundle.user_id

        create_resp = await host_bundle.http.post("/lobbies")
        assert create_resp.status_code == 200
        lobby_id = create_resp.json()["id"]

        update_resp = await host_bundle.http.put(
            f"/lobbies/{lobby_id}",
            json={
                "rounds": 3,
                "max_round_time": 60,
                "difficulty_level": {"rows": 3, "columns": 3, "mine_count": 1},
                "game_mode": "normal",
                "generator": {"type": "random", "settings": None},
            },
        )
        assert update_resp.status_code in [200, 204]

        async with AsyncExitStack() as stack:
            host_notif = await stack.enter_async_context(host_bundle.ws())
            g1_notif = await stack.enter_async_context(g1_bundle.ws())
            g2_notif = await stack.enter_async_context(g2_bundle.ws())

            await receive_type(host_notif, "current_lobby")
            await receive_type(g1_notif, "current_lobby")
            await receive_type(g2_notif, "current_lobby")

            host_lobby = await stack.enter_async_context(
                host_bundle.ws(f"/game/multi/{lobby_id}")
            )

            await receive_type(host_lobby, "session_state")
            await receive_type(host_lobby, "user_ready")

            inv1_resp = await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations", json={"user_id": g1_id}
            )
            assert inv1_resp.status_code == 200
            invitation1 = await receive_type(g1_notif, "invitation")

            inv2_resp = await host_bundle.http.post(
                f"/lobbies/{lobby_id}/invitations", json={"user_id": g2_id}
            )
            assert inv2_resp.status_code == 200
            invitation2 = await receive_type(g2_notif, "invitation")

            g1_lobby = await stack.enter_async_context(
                g1_bundle.ws(
                    f"/game/multi/{lobby_id}?invitation_id={invitation1['id']}"
                )
            )
            await receive_type(g1_lobby, "session_state")
            await receive_type(host_lobby, "invitation_response")
            await receive_type(host_lobby, "user_connection_status")

            await receive_type(g1_lobby, "user_ready")
            await receive_type(g1_lobby, "user_ready")

            g2_lobby = await stack.enter_async_context(
                g2_bundle.ws(
                    f"/game/multi/{lobby_id}?invitation_id={invitation2['id']}"
                )
            )
            await receive_type(g2_lobby, "session_state")

            await receive_type(host_lobby, "invitation_response")
            await receive_type(host_lobby, "user_connection_status")
            await receive_type(g1_lobby, "user_connection_status")

            await receive_type(g2_lobby, "user_ready")
            await receive_type(g2_lobby, "user_ready")
            await receive_type(g2_lobby, "user_ready")

            await host_lobby.send_json({"type": "ready"})
            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "user_ready")

            await g1_lobby.send_json({"type": "ready"})
            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "user_ready")

            await g2_lobby.send_json({"type": "ready"})
            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "user_ready")

            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "round_ready")

            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "round_countdown")

            await g2_notif.close()
            await g2_lobby.close()

            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "user_ready")
                offline_msg = await receive_type(ws, "user_online_status")
                assert offline_msg["user"]["id"] == str(g2_id)
                assert offline_msg["user"]["is_online"] is False

            g2_notif = await stack.enter_async_context(g2_bundle.ws())
            await receive_type(g2_notif, "current_lobby")

            g2_lobby = await stack.enter_async_context(
                g2_bundle.ws(f"/game/multi/{lobby_id}")
            )
            await receive_type(g2_lobby, "session_state")
            for _ in range(3):
                await receive_type(g2_lobby, "user_ready")

            for ws in (host_lobby, g1_lobby):
                online_msg = await receive_type(ws, "user_online_status")
                assert online_msg["user"]["id"] == str(g2_id)
                assert online_msg["user"]["is_online"] is True

            await g2_lobby.send_json({"type": "ready"})
            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "user_ready")

            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "round_ready")

            for ws in (host_lobby, g1_lobby, g2_lobby):
                await receive_type(ws, "round_countdown")

            await fake_scheduler.skip(timedelta(seconds=6))

            await g2_notif.close()
            await g2_lobby.close()

            for ws in (host_lobby, g1_lobby):
                offline_msg = await receive_type(ws, "user_online_status")
                assert offline_msg["user"]["id"] == str(g2_id)
                assert offline_msg["user"]["is_online"] is False

            await fake_scheduler.skip(timedelta(seconds=6))

            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "round_start")

            await asyncio.sleep(1.5)
            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "user_connection_status")

            await fake_scheduler.skip(timedelta(seconds=60))

            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "game_over")
                for _ in range(3):
                    await receive_type(ws, "score_update")
                await receive_type(ws, "round_end")

            await host_lobby.send_json({"type": "ready"})
            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "user_ready")

            await g1_lobby.send_json({"type": "ready"})
            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "user_ready")

            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "round_ready")

            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "round_countdown")

            await fake_scheduler.skip(timedelta(seconds=10))
            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "round_start")

            await fake_scheduler.skip(timedelta(seconds=60))

            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "game_over")
                for _ in range(2):
                    await receive_type(ws, "score_update")
                await receive_type(ws, "round_end")

            for ws in (host_lobby, g1_lobby):
                await receive_type(ws, "session_over")

    finally:
        user_connection_service.REMOVE_OFFLINE_USER_DELAY = backup_delay
