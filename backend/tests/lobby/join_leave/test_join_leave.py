import uuid

import pytest

from backend.tests.utils.test_helpers import create_second_user_and_login


@pytest.mark.anyio
async def test_join_lobby_returns_lobby_response(client, auth):
    host_email = f"joinhost-{uuid.uuid4().hex[:8]}@example.com"
    guest_email = f"joinguest-{uuid.uuid4().hex[:8]}@example.com"

    await auth(email=host_email, password="joinhostpw", nickname="joinhost")
    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    with create_second_user_and_login(
        guest_email, "joinguestpw", "joinguest"
    ) as guest_client:
        guest_me = guest_client.get("/api/auth/me")
        guest_id = guest_me.json()["id"]
        await client.post(
            f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
        )


@pytest.mark.anyio
async def test_join_lobby_without_auth_returns_401(client):
    resp = await client.post(
        f"/api/lobbies/{uuid.uuid4()}/join",
        json={
            "invitation_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_leave_lobby_success(client, auth):
    email = f"leavelobby-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="leavelobbypw", nickname="leavelobbyhost")

    create_resp = await client.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = await client.post(f"/api/lobbies/{lobby_id}/leave")
    assert resp.status_code in [200, 204]


@pytest.mark.anyio
async def test_leave_lobby_without_auth_returns_401(client):
    resp = await client.post(f"/api/lobbies/{uuid.uuid4()}/leave")
    assert resp.status_code == 401
