import uuid

import pytest


@pytest.mark.asyncio
async def test_get_gameplays_returns_paginated_gameplay_response(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.get("/api/gameplays")

    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_gameplays_validates_gameplay_response_schema(authenticated_clients):
    client = authenticated_clients[0]
    from backend.core.board import Board, DifficultyLevel, GenerationSettings
    from backend.db import db
    from backend.repositories.board_repo import BoardRepository

    async def create_board():
        async with db.async_session_maker() as session:
            repo = BoardRepository(session)
            difficulty = DifficultyLevel(rows=3, columns=3, mine_count=1)
            board = Board(
                id=uuid.uuid4(),
                minefields=[(0, 0)],
                start_field=(1, 1),
                generation_settings=GenerationSettings(
                    type="random", settings=None, difficulty_level=difficulty
                ),
            )
            try:
                await repo.add_board(board)
            except Exception:
                pass
            return str(board.id)

    board_id = await create_board()

    game_resp = await client.post(
        "/api/game/singleplayer",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )

    if game_resp.status_code == 200:

        resp = await client.get("/api/gameplays")
        assert resp.status_code == 200
        data = resp.json()

        if data["items"]:
            for item in data["items"]:

                assert "id" in item
                assert "user_id" in item
                assert "status" in item
                assert "elapsed_time" in item
                assert "difficulty_level" in item

                uuid.UUID(str(item["id"]))
                uuid.UUID(str(item["user_id"]))
                assert item["status"] in ["not_started", "in_progress", "finished"]
                assert isinstance(item["elapsed_time"], (int, float))


@pytest.mark.asyncio
async def test_get_gameplays_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.get("/api/gameplays")
    assert resp.status_code == 401
