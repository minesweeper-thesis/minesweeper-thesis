import uuid

import pytest


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_400(client_no_auth):
    email = f"badlogin-{uuid.uuid4().hex[:8]}@example.com"

    await client_no_auth.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correctpassword",
            "nickname": "badlogintest",
            "settings": {},
        },
    )

    resp = await client_no_auth.post(
        "/auth/login",
        data={
            "username": email,
            "password": "wrongpassword",
        },
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "LOGIN_BAD_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_nonexistent_user_returns_400(client_no_auth):
    resp = await client_no_auth.post(
        "/auth/login",
        data={
            "username": f"noexist-{uuid.uuid4().hex[:8]}@example.com",
            "password": "anypassword",
        },
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "LOGIN_BAD_CREDENTIALS"
