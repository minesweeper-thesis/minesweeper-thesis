import uuid

import pytest


@pytest.mark.asyncio
async def test_logout_clears_auth_cookie(http_client):
    email = f"logout-{uuid.uuid4().hex[:8]}@example.com"

    await http_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "mypassword",
            "nickname": "logouttest",
            "settings": {},
        },
    )

    login_resp = await http_client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "mypassword",
        },
    )
    assert login_resp.status_code == 204
    assert "auth" in login_resp.cookies

    logout_resp = await http_client.post("/auth/logout")
    assert logout_resp.status_code == 204

    auth_cookie = logout_resp.cookies.get("auth")
    assert auth_cookie == "" or auth_cookie is None or "auth" not in logout_resp.cookies


@pytest.mark.asyncio
async def test_logout_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post("/auth/logout")
    assert resp.status_code == 401
