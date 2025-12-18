import pytest
from httpx import AsyncClient
from httpx_ws import HTTPXWSException, aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport


@pytest.mark.asyncio
async def test_notifications_websocket_connect_returns_current_lobby_response(
    authenticated_clients,
):
    bundle = authenticated_clients[0]

    async with bundle.ws() as ws:
        data = await ws.receive_json()

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

    async with bundle.ws() as ws:
        data = await ws.receive_json()

    assert data["type"] == "current_lobby"

    lobby = data["lobby"]
    if lobby is not None:
        assert lobby["id"] == lobby_id
        assert lobby["host"]["nickname"] == bundle.user_data["nickname"]


@pytest.mark.asyncio
async def test_notifications_websocket_without_auth_fails(test_app):
    transport = ASGIWebSocketTransport(test_app)
    async with AsyncClient(
        transport=transport, base_url="https://testserver"
    ) as client:
        with pytest.raises(HTTPXWSException):
            async with aconnect_ws("https://testserver/api/ws", client):
                pass
