import uuid

from backend.routers.schemas.user import CurrentUserResponse


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
