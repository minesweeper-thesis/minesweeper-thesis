import asyncio

import pytest

from backend.tests.user.gameplay_factory import create_gameplay_via_service
from backend.tests.utils.auth_helpers import register_and_login


@pytest.mark.asyncio
async def test_get_gameplays_empty(client):
    loop = asyncio.get_running_loop()
    user = await loop.run_in_executor(
        None, register_and_login, client, "gp_empty@example.com"
    )

    resp = await loop.run_in_executor(None, client.get, "/api/gameplays")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_gameplays_with_items(client):
    loop = asyncio.get_running_loop()
    user = await loop.run_in_executor(
        None, register_and_login, client, "gp_items@example.com"
    )
    user_id = user["id"]

    # create 3 gameplays for this user via async service helper
    for _ in range(3):
        await create_gameplay_via_service(user_id)

    resp = await loop.run_in_executor(None, client.get, "/api/gameplays?size=2&page=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) <= 2
    # check item fields
    if data["items"]:
        item = data["items"][0]
        assert "id" in item
        assert "board_id" in item
        assert "status" in item
        assert "used_hints" in item
        assert "elapsed_time" in item
        assert "game_mode" in item
