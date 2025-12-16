import uuid

import pytest


@pytest.mark.asyncio
async def test_send_chat_message_success(authenticated_clients):
    client = authenticated_clients[0]
    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "Hello lobby!",
        },
    )
    assert resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_send_empty_chat_message(authenticated_clients):
    client = authenticated_clients[0]
    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "",
        },
    )

    assert resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_send_chat_message_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post(
        f"/api/lobbies/{uuid.uuid4()}/chat-messages",
        json={
            "content": "Hello!",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_chat_messages_returns_list(authenticated_clients):
    client = authenticated_clients[0]
    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    await client.post(
        f"/api/lobbies/{lobby_id}/chat-messages",
        json={
            "content": "Test message",
        },
    )

    resp = await client.get(f"/api/lobbies/{lobby_id}/chat-messages")

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


@pytest.mark.asyncio
async def test_get_chat_messages_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.get(f"/api/lobbies/{uuid.uuid4()}/chat-messages")
    assert resp.status_code == 401
