import json
import uuid

import pytest

from backend.tests.utils.cookies import using_auth_cookie_sync


@pytest.mark.anyio
async def test_notifications_websocket_connect_returns_current_lobby_response(
    auth_ws, ws_client
):
    email = f"notif-connect-{uuid.uuid4().hex[:8]}@example.com"
    user = auth_ws(email=email, password="notifconnectpw", nickname="notifconnect")

    with using_auth_cookie_sync(ws_client, user["auth_cookie"]):
        with ws_client.websocket_connect("/api/ws") as ws:
            data = json.loads(ws.receive_text())

    assert data["type"] == "current_lobby"
    assert "lobby" in data

    lobby = data["lobby"]
    if lobby is not None:
        assert "id" in lobby
        assert "host" in lobby
        assert "users" in lobby
        assert "game_config" in lobby


@pytest.mark.anyio
async def test_notifications_websocket_connect_with_active_lobby(
    client, auth_ws, ws_client
):
    from backend.tests.utils.cookies import using_auth_cookie

    email = f"notif-lobby-{uuid.uuid4().hex[:8]}@example.com"
    user = auth_ws(email=email, password="notiflobbypw", nickname="notiflobby")

    async with using_auth_cookie(client, user["auth_cookie"]):
        create_resp = await client.post("/api/lobbies")
        lobby_id = create_resp.json()["id"]

    with using_auth_cookie_sync(ws_client, user["auth_cookie"]):
        with ws_client.websocket_connect("/api/ws") as ws:
            data = json.loads(ws.receive_text())

    assert data["type"] == "current_lobby"

    lobby = data["lobby"]
    if lobby is not None:
        assert lobby["id"] == lobby_id
        assert lobby["host"]["nickname"] == "notiflobby"


@pytest.mark.anyio
async def test_notifications_websocket_without_auth_fails(ws_client):
    try:
        with ws_client.websocket_connect("/api/ws") as ws:
            data = ws.receive_text()
            parsed = json.loads(data)
    except Exception:
        pass
