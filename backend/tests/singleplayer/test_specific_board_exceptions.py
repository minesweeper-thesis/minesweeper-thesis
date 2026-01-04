import pytest

from backend.tests.singleplayer.helpers import create_board


@pytest.mark.asyncio(loop_scope="session")
async def test_anonymous_cannot_create_specific_board(client_no_auth):
    board_id, _ = await create_board(rows=3, columns=3, mine_count=1)

    resp = await client_no_auth.post(
        "/game/single",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )

    assert resp.status_code == 400


@pytest.mark.asyncio(loop_scope="session")
async def test_authenticated_cannot_create_same_board_twice(authenticated_clients):
    bundle = authenticated_clients[0]
    board_id, _ = await create_board(rows=3, columns=3, mine_count=1)

    resp1 = await bundle.http.post(
        "/game/single",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )
    assert resp1.status_code == 200

    resp2 = await bundle.http.post(
        "/game/single",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )
    assert resp2.status_code == 400
