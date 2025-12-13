import uuid

import pytest


@pytest.mark.anyio
async def test_get_me_without_auth_returns_401(client):
    """GET /me without auth returns 401."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_patch_me_without_auth_returns_401(client):
    """PATCH /me without auth returns 401."""
    resp = await client.patch(
        "/api/auth/me",
        json={
            "nickname": "hacker",
            "settings": {},
        },
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_delete_user_by_id_requires_superuser(client, auth):
    """DELETE /auth/{id} requires superuser - regular users get 403."""
    email = f"deleteme-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="deletepw", nickname="deleteuser")

    # Get the user id from /me
    me_resp = await client.get("/api/auth/me")
    assert me_resp.status_code == 200
    user_id = me_resp.json()["id"]

    # Regular user trying to delete themselves gets 403
    resp = await client.delete(f"/api/auth/{user_id}")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_delete_me_without_auth_returns_401(client):
    """DELETE /me without auth returns 401."""
    resp = await client.delete("/api/auth/me")
    assert resp.status_code == 401
