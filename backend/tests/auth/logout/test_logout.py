import pytest


@pytest.mark.asyncio
async def test_logout_clears_auth_cookie(authenticated_clients):
    client = authenticated_clients[0]
    assert "auth" in client.cookies

    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 204
    assert "auth" not in client.cookies or client.cookies.get("auth") == ""


@pytest.mark.asyncio
async def test_logout_without_auth_returns_401(client):
    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 401
