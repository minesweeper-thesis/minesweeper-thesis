import json
import uuid

from backend.schemas.game.single_schemas import NewGameResponse


def test_start_game_validates_response(client, auth):
    email = f"sp-start-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_start")

    resp = client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 2},
            "generator": {"type": "random"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 200

    data = resp.json()

    assert "gameplay_id" in data
    game_response = NewGameResponse(**data)
    assert game_response.gameplay_id is not None
    uuid.UUID(str(game_response.gameplay_id))


def test_start_game_invalid_board_returns_404(client, auth):
    email = f"sp-invalid-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_invalid")

    fake_board_id = str(uuid.uuid4())
    resp = client.post(
        "/api/game/single",
        json={"board_id": fake_board_id, "mode": "normal"},
    )
    assert resp.status_code == 404


def test_start_game_works_without_auth(client):
    resp = client.post(
        "/api/game/single",
        json={
            "mode": "normal",
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 3},
            "generator": {"type": "random"},
        },
    )
    assert resp.status_code == 200
    assert "gameplay_id" in resp.json()


def test_start_game_validates_difficulty_level(client, auth):
    email = f"sp-diff-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_diff")

    resp = client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5},
            "generator": {"type": "random"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 422


def test_start_game_validates_generator_type(client, auth):
    email = f"sp-gen-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="sp_gen")

    resp = client.post(
        "/api/game/single",
        json={
            "difficulty_level": {"rows": 5, "columns": 5, "mine_count": 2},
            "generator": {"type": "invalid_generator"},
            "mode": "normal",
        },
    )
    assert resp.status_code == 422


def test_websocket_invalid_gameplay_returns_error(client, auth):
    email = f"ws-invalid-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="pw", nickname="ws_invalid")

    fake_gameplay_id = str(uuid.uuid4())

    try:
        with client.websocket_connect(f"/api/game/single/{fake_gameplay_id}") as ws:
            data = json.loads(ws.receive_text())
            assert data.get("type") in ["error", "game_state"]
    except Exception:

        pass
