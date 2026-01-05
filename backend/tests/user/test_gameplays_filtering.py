import uuid

import pytest

from backend.core.board import Board, DifficultyLevel, GenerationSettings
from backend.core.single.single_gameplay import SingleplayerGameplay
from backend.db import db
from backend.protocols.repos.board_repo_protocol import BoardNotFound
from backend.repositories.board_repo import BoardRepository
from backend.repositories.singleplayer_repo import SingleplayerRepository


@pytest.mark.asyncio(loop_scope="session")
async def test_get_gameplays_filtering(authenticated_clients):
    client = authenticated_clients[0]
    user_id = uuid.UUID(client.user_id)

    async with db.async_session_maker() as session:
        board_repo = BoardRepository(session)
        sp_repo = SingleplayerRepository(session)

        difficulty = DifficultyLevel(rows=3, columns=3, mine_count=1)
        settings = GenerationSettings(
            type="random", settings=None, difficulty_level=difficulty
        )
        try:
            board = await board_repo.get_board(difficulty, [(0, 0)])
        except BoardNotFound:
            board = Board(
                id=uuid.uuid4(),
                minefields=[(0, 0)],
                start_field=(1, 1),
                generation_settings=settings,
            )
            await board_repo.add_board(board)

        gp1 = SingleplayerGameplay(
            id=uuid.uuid4(),
            board=board,
            status="finished",
            result="win",
            used_hints=False,
            elapsed_time=10.0,
            mode="normal",
        )
        await sp_repo.add_gameplay(gp1, board.id, user_id)

        gp2 = SingleplayerGameplay(
            id=uuid.uuid4(),
            board=board,
            status="finished",
            result="loss",
            used_hints=True,
            elapsed_time=20.0,
            mode="hardcore",
        )
        await sp_repo.add_gameplay(gp2, board.id, user_id)

        gp3 = SingleplayerGameplay(
            id=uuid.uuid4(),
            board=board,
            status="in_progress",
            result=None,
            used_hints=False,
            elapsed_time=5.0,
            mode="normal",
        )
        await sp_repo.add_gameplay(gp3, board.id, user_id)

    resp = await client.http.get("/gameplays", params={"status": "finished"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 2
    assert all(i["status"] == "finished" for i in items)

    resp = await client.http.get("/gameplays", params={"result": "win"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(i["id"] == str(gp1.id) for i in items)
    assert all(i["result"] == "win" for i in items)

    resp = await client.http.get("/gameplays", params={"used_hints": True})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(i["id"] == str(gp2.id) for i in items)
    assert all(i["used_hints"] for i in items)

    resp = await client.http.get("/gameplays", params={"mode": "hardcore"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(i["id"] == str(gp2.id) for i in items)
    assert all(i["game_mode"] == "hardcore" for i in items)

    resp = await client.http.get(
        "/gameplays", params={"min_time": 15.0, "max_time": 25.0}
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(i["id"] == str(gp2.id) for i in items)
    assert all(15.0 <= i["elapsed_time"] <= 25.0 for i in items)

    resp = await client.http.get(
        "/gameplays",
        params={"status": "finished", "result": "loss", "mode": "hardcore"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(i["id"] == str(gp2.id) for i in items)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_gameplays_sorting(authenticated_clients):
    client = authenticated_clients[0]
    user_id = uuid.UUID(client.user_id)

    async with db.async_session_maker() as session:
        board_repo = BoardRepository(session)
        sp_repo = SingleplayerRepository(session)

        difficulty = DifficultyLevel(rows=3, columns=3, mine_count=1)
        settings = GenerationSettings(
            type="random", settings=None, difficulty_level=difficulty
        )
        try:
            board = await board_repo.get_board(difficulty, [(0, 0)])
        except BoardNotFound:
            board = Board(
                id=uuid.uuid4(),
                minefields=[(0, 0)],
                start_field=(1, 1),
                generation_settings=settings,
            )
            await board_repo.add_board(board)

        gp_fast = SingleplayerGameplay(id=uuid.uuid4(), board=board, elapsed_time=5.0)
        gp_slow = SingleplayerGameplay(id=uuid.uuid4(), board=board, elapsed_time=50.0)
        gp_mid = SingleplayerGameplay(id=uuid.uuid4(), board=board, elapsed_time=25.0)

        for gp in [gp_fast, gp_slow, gp_mid]:
            await sp_repo.add_gameplay(gp, board.id, user_id)

    resp = await client.http.get("/gameplays", params={"order_by": "time_asc"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    times = [i["elapsed_time"] for i in items]
    assert times == sorted(times)

    resp = await client.http.get("/gameplays", params={"order_by": "time_desc"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    times = [i["elapsed_time"] for i in items]
    assert times == sorted(times, reverse=True)
