import json

import pytest
from fastapi import WebSocketDisconnect


@pytest.mark.asyncio
async def test_notifications_websocket_connect_returns_current_lobby_response(
    authenticated_clients,
):
    bundle = authenticated_clients[0]

    with bundle.get_ws() as ws:
        data = json.loads(ws.receive_text())

    assert data["type"] == "current_lobby"
    assert "lobby" in data

    lobby = data["lobby"]
    if lobby is not None:
        assert "id" in lobby
        assert "host" in lobby
        assert "users" in lobby
        assert "game_config" in lobby


@pytest.mark.asyncio
async def test_notifications_websocket_connect_with_active_lobby(authenticated_clients):
    bundle = authenticated_clients[0]

    create_resp = await bundle.http.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    with bundle.get_ws() as ws:
        data = json.loads(ws.receive_text())

    assert data["type"] == "current_lobby"

    lobby = data["lobby"]
    if lobby is not None:
        assert lobby["id"] == lobby_id
        assert lobby["host"]["nickname"] == bundle.user_data["nickname"]


@pytest.mark.asyncio
async def test_notifications_websocket_without_auth_fails(ws_client_no_auth):
    with pytest.raises(WebSocketDisconnect):
        with ws_client_no_auth.websocket_connect("/api/ws"):
            pass
