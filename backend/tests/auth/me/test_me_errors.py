import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_get_me_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_patch_me_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.patch(
        "/auth/me",
        json={
            "nickname": "hacker",
            "settings": {},
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_me_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.delete("/auth/me")
    assert resp.status_code == 401
