import uuid

import pytest

from backend.schemas.user import CurrentUserResponse


@pytest.mark.asyncio
async def test_get_me_returns_current_user_response(client, auth):
    email = f"getme-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="getmepw", nickname="getmeuser")

    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200

    data = resp.json()
    user = CurrentUserResponse(**data)

    assert user.email == email
    assert user.nickname == "getmeuser"


@pytest.mark.asyncio
async def test_patch_me_updates_nickname(client, auth):
    email = f"patchme-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="patchpw", nickname="oldnick")

    resp = await client.patch(
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


@pytest.mark.asyncio
async def test_patch_me_updates_settings(client, auth):
    email = f"patchsettings-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="patchpw", nickname="settingsuser")

    new_settings = {"theme": "light", "language": "pl"}
    resp = await client.patch(
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
