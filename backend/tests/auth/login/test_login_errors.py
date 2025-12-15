import uuid

import pytest


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_400(client):
    email = f"badlogin-{uuid.uuid4().hex[:8]}@example.com"

    await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "correctpassword",
            "nickname": "badlogintest",
            "settings": {},
        },
    )

    resp = await client.post(
        "/api/auth/login",
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
async def test_login_nonexistent_user_returns_400(client):
    resp = await client.post(
        "/api/auth/login",
        data={
            "username": f"noexist-{uuid.uuid4().hex[:8]}@example.com",
            "password": "anypassword",
        },
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "LOGIN_BAD_CREDENTIALS"
