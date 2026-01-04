import uuid

import pytest

from backend.schemas.user import CurrentUserResponse
from backend.tests.conftest import HTTPClient


@pytest.mark.asyncio(loop_scope="session")
async def test_login_success_sets_auth_cookie_and_me_returns_user(
    client_no_auth: HTTPClient,
):
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"

    await client_no_auth.post(
        "/auth/register",
        json={
            "email": email,
            "password": "mypassword",
            "nickname": "logintest",
            "settings": {},
        },
    )

    resp = await client_no_auth.post(
        "/auth/login",
        data={
            "username": email,
            "password": "mypassword",
        },
    )

    assert resp.status_code == 204 or resp.status_code == 200
    assert "auth" in resp.cookies

    client_no_auth._auth_cookie = resp.cookies.get("auth")

    me_resp = await client_no_auth.get("/auth/me")
    assert me_resp.status_code == 200
    user = CurrentUserResponse(**me_resp.json())
    assert user.email == email
    assert user.id is not None
