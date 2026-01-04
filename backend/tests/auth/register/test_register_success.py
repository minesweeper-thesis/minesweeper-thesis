import uuid

import pytest

from backend.schemas.user import CurrentUserResponse


@pytest.mark.asyncio(loop_scope="session")
async def test_register_success_validates_current_user_response(client_no_auth):
    email = f"reg-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "strongpassword123",
        "nickname": "test_user",
        "settings": {"theme": "dark"},
    }

    resp = await client_no_auth.post("/auth/register", json=payload)

    assert resp.status_code == 201
    data = resp.json()

    user = CurrentUserResponse(**data)
    assert user.email == email
    assert user.nickname == "test_user"
    assert user.id is not None
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.is_verified is False
    assert user.settings == {"theme": "dark"}
    assert user.avatar_url is None

    uuid.UUID(str(user.id))


@pytest.mark.asyncio(loop_scope="session")
async def test_login_success_sets_auth_cookie(client_no_auth):
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
