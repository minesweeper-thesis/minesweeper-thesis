
import uuid

def test_set_ready_in_lobby(client, auth):
    email = f"readylobby-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="readylobbypw", nickname="readylobbyhost")

    create_resp = client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = client.post(f"/api/lobbies/{lobby_id}/ready/set")

    assert resp.status_code in [200, 204, 400]

def test_set_ready_without_auth_returns_401(client):
    resp = client.post(f"/api/lobbies/{uuid.uuid4()}/ready/set")
    assert resp.status_code == 401
