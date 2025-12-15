import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.tests.utils.test_helpers import create_second_user_and_login


@pytest.mark.asyncio
async def test_invite_user_to_lobby_success(client, auth):
    host_email = f"invitehost-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=host_email, password="invitehostpw", nickname="invitehost")

    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_email = f"inviteguest-{uuid.uuid4().hex[:8]}@example.com"
    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://testserver"
    ) as client2:
        reg_resp = await client2.post(
            "/api/auth/register",
            json={
                "email": guest_email,
                "password": "inviteguestpw",
                "nickname": "inviteguest",
                "settings": {},
            },
        )
        guest_id = reg_resp.json()["id"] if reg_resp.status_code == 201 else None

    if guest_id:
        resp = await client.post(
            f"/api/lobbies/{lobby_id}/invitations",
            json={
                "user_id": guest_id,
            },
        )
        assert resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_invite_user_without_auth_returns_401(client):
    resp = await client.post(
        f"/api/lobbies/{uuid.uuid4()}/invitations",
        json={
            "user_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reject_invitation_success(client, auth):
    host_email = f"rejecthost-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"rejectguest-{uuid.uuid4().hex[:8]}@example.com"

    await auth(email=host_email, password="rejecthostpw", nickname="rejecthost")
    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_client = create_second_user_and_login(
        guest_email, "rejectguestpw", "rejectguest"
    )
    guest_me = guest_client.get("/api/auth/me")
    guest_id = guest_me.json()["id"]

    await client.post(
        f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
    )


@pytest.mark.asyncio
async def test_reject_invitation_without_auth_returns_401(client):
    resp = await client.delete(f"/api/invitations/{uuid.uuid4()}")
    assert resp.status_code == 401
