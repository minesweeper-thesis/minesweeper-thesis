import pytest

from backend.schemas.user import CurrentUserResponse


@pytest.mark.asyncio
async def test_get_me_returns_current_user_response(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200

    data = resp.json()
    user = CurrentUserResponse(**data)

    assert user.email == "test@example.com"
    assert user.nickname == "test"


@pytest.mark.asyncio
async def test_patch_me_updates_nickname(authenticated_clients):
    client = authenticated_clients[0]
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
async def test_patch_me_updates_settings(authenticated_clients):
    client = authenticated_clients[0]
    new_settings = {"theme": "light", "language": "pl"}
    resp = await client.patch(
        "/api/auth/me",
        json={
            "nickname": "test",
            "settings": new_settings,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    user = CurrentUserResponse(**data)
    assert user.settings == new_settings
