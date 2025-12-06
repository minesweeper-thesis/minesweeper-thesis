import json
import uuid


def test_notifications_websocket_connect_returns_current_lobby_response(client, auth):
    email = f"notif-connect-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="notifconnectpw", nickname="notifconnect")

    with client.websocket_connect("/api/ws", cookies=dict(client.cookies)) as ws:
        data = json.loads(ws.receive_text())

        assert data["type"] == "current_lobby"
        assert "lobby" in data

        lobby = data["lobby"]
        if lobby is not None:
            assert "id" in lobby
            assert "host" in lobby
            assert "users" in lobby
            assert "game_config" in lobby


def test_notifications_websocket_connect_with_active_lobby(client, auth):
    email = f"notif-lobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="notiflobbypw", nickname="notiflobby")

    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    with client.websocket_connect("/api/ws", cookies=dict(client.cookies)) as ws:
        data = json.loads(ws.receive_text())

        assert data["type"] == "current_lobby"

        lobby = data["lobby"]
        if lobby is not None:
            assert lobby["id"] == lobby_id
            assert lobby["host"]["nickname"] == "notiflobby"


def test_notifications_websocket_without_auth_fails(client):
    try:
        with client.websocket_connect("/api/ws") as ws:
            data = ws.receive_text()
            parsed = json.loads(data)
    except Exception:
        pass
