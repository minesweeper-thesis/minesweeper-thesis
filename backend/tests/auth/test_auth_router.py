"""
Comprehensive auth router tests.
Tests: POST /register, POST /login, POST /logout, GET /me, PATCH /me, DELETE /me
"""

import uuid

from backend.routers.schemas.user import CurrentUserResponse

# =============================================================================
# POST /register Tests
# =============================================================================


def test_register_success_validates_current_user_response(client):
    """POST /register - validates full CurrentUserResponse schema."""
    email = f"reg-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "strongpassword123",
        "nickname": "test_user",
        "settings": {"theme": "dark"},
    }

    resp = client.post("/api/auth/register", json=payload)

    assert resp.status_code == 201
    data = resp.json()

    # Validate full CurrentUserResponse schema
    user = CurrentUserResponse(**data)
    assert user.email == email
    assert user.nickname == "test_user"
    assert user.id is not None
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.is_verified is False
    assert user.settings == {"theme": "dark"}
    assert user.avatar_url is None

    # Validate ID is proper UUID
    uuid.UUID(str(user.id))


def test_register_duplicate_email_returns_400(client):
    """POST /register with duplicate email returns 400 REGISTER_USER_ALREADY_EXISTS."""
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "secret123",
        "nickname": "first_user",
        "settings": {},
    }

    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    payload["nickname"] = "second_user"
    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 400

    data = resp2.json()
    assert "detail" in data
    assert data["detail"] == "REGISTER_USER_ALREADY_EXISTS"


def test_register_with_short_password_succeeds(client):
    """POST /register with short password - API accepts it (no min length validation)."""
    payload = {
        "email": f"short-{uuid.uuid4().hex[:8]}@example.com",
        "password": "ab",  # Short password - API accepts it
        "nickname": "shortpw",
        "settings": {},
    }

    resp = client.post("/api/auth/register", json=payload)
    # fastapi-users doesn't enforce minimum password length by default
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload["email"]


def test_register_missing_required_field_returns_422(client):
    """POST /register missing required field returns 422 with validation error."""
    # Missing password
    payload = {
        "email": f"nopw-{uuid.uuid4().hex[:8]}@example.com",
        "nickname": "nopassword",
        "settings": {},
    }

    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 422

    data = resp.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    # Validation error should mention missing field
    field_names = [err.get("loc", [])[-1] for err in data["detail"]]
    assert "password" in field_names


def test_register_invalid_email_format_returns_422(client):
    """POST /register with invalid email format returns 422."""
    payload = {
        "email": "not-an-email",
        "password": "validpassword",
        "nickname": "bademail",
        "settings": {},
    }

    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 422


# =============================================================================
# POST /login Tests
# =============================================================================


def test_login_success_sets_auth_cookie(client):
    """POST /login with valid credentials sets auth cookie."""
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"

    # First register
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "mypassword",
            "nickname": "logintest",
            "settings": {},
        },
    )

    # Then login
    resp = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": "mypassword",
        },
    )

    assert resp.status_code == 204 or resp.status_code == 200
    assert "auth" in client.cookies


def test_login_invalid_credentials_returns_400(client):
    """POST /login with wrong password returns 400 LOGIN_BAD_CREDENTIALS."""
    email = f"badlogin-{uuid.uuid4().hex[:8]}@example.com"

    # Register first
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "correctpassword",
            "nickname": "badlogintest",
            "settings": {},
        },
    )

    # Try login with wrong password
    resp = client.post(
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


def test_login_nonexistent_user_returns_400(client):
    """POST /login with non-existent user returns 400."""
    resp = client.post(
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


# =============================================================================
# POST /logout Tests
# =============================================================================


def test_logout_clears_auth_cookie(client, auth):
    """POST /logout clears auth cookie."""
    email = f"logout-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="logoutpw", nickname="logoutuser")

    assert "auth" in client.cookies

    resp = client.post("/api/auth/logout")
    assert resp.status_code == 204
    # Cookie should be cleared or expired
    assert "auth" not in client.cookies or client.cookies.get("auth") == ""


def test_logout_without_auth_returns_401(client):
    """POST /logout without being logged in returns 401."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401


# =============================================================================
# GET /me Tests
# =============================================================================


def test_get_me_returns_current_user_response(client, auth):
    """GET /me returns full CurrentUserResponse for logged in user."""
    email = f"getme-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="getmepw", nickname="getmeuser")

    resp = client.get("/api/auth/me")
    assert resp.status_code == 200

    data = resp.json()
    user = CurrentUserResponse(**data)

    assert user.email == email
    assert user.nickname == "getmeuser"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.is_verified is False


def test_get_me_without_auth_returns_401(client):
    """GET /me without auth returns 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


# =============================================================================
# PATCH /me Tests
# =============================================================================


def test_patch_me_updates_nickname(client, auth):
    """PATCH /me updates user nickname."""
    email = f"patchme-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="patchpw", nickname="oldnick")

    resp = client.patch(
        "/api/auth/me",
        json={
            "nickname": "newnickname",
            "settings": {},
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    user = CurrentUserResponse(**data)
    assert user.nickname == "newnickname"


def test_patch_me_updates_settings(client, auth):
    """PATCH /me updates user settings."""
    email = f"patchsettings-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="patchpw", nickname="settingsuser")

    new_settings = {"theme": "light", "language": "pl"}
    resp = client.patch(
        "/api/auth/me",
        json={
            "nickname": "settingsuser",
            "settings": new_settings,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    user = CurrentUserResponse(**data)
    assert user.settings == new_settings


def test_patch_me_without_auth_returns_401(client):
    """PATCH /me without auth returns 401."""
    resp = client.patch(
        "/api/auth/me",
        json={
            "nickname": "hacker",
            "settings": {},
        },
    )
    assert resp.status_code == 401


# =============================================================================
# DELETE /me Tests
# =============================================================================


def test_delete_user_by_id_requires_superuser(client, auth):
    """DELETE /auth/{id} requires superuser - regular users get 403."""
    email = f"deleteme-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="deletepw", nickname="deleteuser")

    # Get the user id from /me
    me_resp = client.get("/api/auth/me")
    assert me_resp.status_code == 200
    user_id = me_resp.json()["id"]

    # Regular user trying to delete themselves gets 403
    resp = client.delete(f"/api/auth/{user_id}")
    assert resp.status_code == 403


def test_delete_me_without_auth_returns_401(client):
    """DELETE /me without auth returns 401."""
    resp = client.delete("/api/auth/me")
    assert resp.status_code == 401
