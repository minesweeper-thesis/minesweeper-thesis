
import uuid

def test_send_chat_message_success(client, auth):
    email = f"chatlobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="chatlobbypw", nickname="chatlobbyhost")

    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "Hello lobby!",
        },
    )
    assert resp.status_code in [200, 204]

def test_send_empty_chat_message(client, auth):
    email = f"emptychat-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="emptychatpw", nickname="emptychathost")

    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "",
        },
    )

    assert resp.status_code in [200, 204, 422]

def test_send_chat_message_without_auth_returns_401(client):
    resp = client.post(
        f"/api/lobbies/{uuid.uuid4()}/chat-messages",
        json={
            "content": "Hello!",
        },
    )
    assert resp.status_code == 401

def test_get_chat_messages_returns_list(client, auth):
    email = f"getchat-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="getchatpw", nickname="getchathost")

    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "Test message",
        },
    )

    resp = client.get(f"/api/lobbies/{lobby_id}/chat-messages")

    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data

    if len(data["items"]) > 0:
        msg = data["items"][0]

        assert "type" in msg
        assert msg["type"] == "lobby_chat_message"
        assert "sender" in msg
        assert "lobby_id" in msg
        assert "content" in msg
        assert "timestamp" in msg

        sender = msg["sender"]
        assert "id" in sender
        assert "nickname" in sender

        assert isinstance(msg["content"], str)
        assert isinstance(msg["timestamp"], int)

def test_get_chat_messages_without_auth_returns_401(client):
    resp = client.get(f"/api/lobbies/{uuid.uuid4()}/chat-messages")
    assert resp.status_code == 401
