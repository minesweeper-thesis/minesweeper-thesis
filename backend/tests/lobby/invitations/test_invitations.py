import uuid

import pytest


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"invitehost-{uuid.uuid4().hex[:8]}@example.com",
                "password": "invitehostpw",
                "nickname": "invitehost",
            },
            {
                "email": f"inviteguest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "inviteguestpw",
                "nickname": "inviteguest",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_invite_user_to_lobby_success(authenticated_clients):
    client1, client2 = authenticated_clients

    create_resp = await client1.http.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_resp = await client2.http.get("/api/auth/me")
    guest_id = guest_resp.json()["id"]

    resp = await client1.http.post(
        f"/api/lobbies/{lobby_id}/invitations",
        json={
            "user_id": guest_id,
        },
    )
    assert resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_invite_user_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post(
        f"/api/lobbies/{uuid.uuid4()}/invitations",
        json={
            "user_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"rejecthost-{uuid.uuid4().hex[:8]}@example.com",
                "password": "rejecthostpw",
                "nickname": "rejecthost",
            },
            {
                "email": f"rejectguest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "rejectguestpw",
                "nickname": "rejectguest",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_reject_invitation_success(authenticated_clients):
    client1, client2 = authenticated_clients

    create_resp = await client1.http.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_me = await client2.http.get("/api/auth/me")
    guest_id = guest_me.json()["id"]

    await client1.http.post(
        f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
    )


@pytest.mark.asyncio
async def test_reject_invitation_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.delete(f"/api/invitations/{uuid.uuid4()}")
    assert resp.status_code == 401
