
import uuid

from fastapi.testclient import TestClient

from backend.main import app

def _create_second_user_and_login(email, password, nickname):
    client = TestClient(app, base_url="https://testserver")
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "nickname": nickname,
            "settings": {},
        },
    )
    client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )
    return client

def test_join_lobby_returns_lobby_response(client, auth):
    host_email = f"joinhost-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"joinguest-{uuid.uuid4().hex[:8]}@example.com"

    auth(email=host_email, password="joinhostpw", nickname="joinhost")
    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_client = _create_second_user_and_login(
        guest_email, "joinguestpw", "joinguest"
    )
    guest_me = guest_client.get("/api/auth/me")
    guest_id = guest_me.json()["id"]

    client.post(f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id})

def test_join_lobby_without_auth_returns_401(client):
    resp = client.post(
        f"/api/lobbies/{uuid.uuid4()}/join",
        json={
            "invitation_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401

def test_leave_lobby_success(client, auth):
    email = f"leavelobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="leavelobbypw", nickname="leavelobbyhost")

    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = client.post(f"/api/lobbies/{lobby_id}/leave")
    assert resp.status_code in [200, 204]

def test_leave_lobby_without_auth_returns_401(client):
    resp = client.post(f"/api/lobbies/{uuid.uuid4()}/leave")
    assert resp.status_code == 401
