import pytest

from backend.schemas.user import CurrentUserResponse


@pytest.mark.asyncio
async def test_get_me_returns_current_user_response(authenticated_clients):
    bundle = authenticated_clients[0]
    resp = await bundle.http.get("/auth/me")
    assert resp.status_code == 200

    data = resp.json()
    user = CurrentUserResponse(**data)

    assert user.email == bundle.user_data["email"]
    assert user.nickname == bundle.user_data["nickname"]


@pytest.mark.asyncio
async def test_patch_me_updates_nickname(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.http.patch(
        "/auth/me",
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
    resp = await client.http.patch(
        "/auth/me",
        json={
            "nickname": "test",
            "settings": new_settings,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    user = CurrentUserResponse(**data)
    assert user.settings == new_settings
