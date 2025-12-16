import pytest


@pytest.mark.asyncio
async def test_get_me_without_auth_returns_401(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_patch_me_without_auth_returns_401(client):
    resp = await client.patch(
        "/api/auth/me",
        json={
            "nickname": "hacker",
            "settings": {},
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_delete_me_without_auth_returns_401(client):
    resp = await client.delete("/api/auth/me")
    assert resp.status_code == 401
