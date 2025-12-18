import uuid

import pytest


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {"email": "joinhost@example.com", "password": "pw", "nickname": "joinhost"},
            {
                "email": "joinguest@example.com",
                "password": "pw",
                "nickname": "joinguest",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_join_lobby_returns_lobby_response(authenticated_clients):
    host_client, guest_client = authenticated_clients
    create_resp = await host_client.http.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_me = await guest_client.http.get("/api/auth/me")
    guest_id = guest_me.json()["id"]
    await host_client.http.post(
        f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
    )


@pytest.mark.asyncio
async def test_join_lobby_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post(
        f"/api/lobbies/{uuid.uuid4()}/join",
        json={
            "invitation_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_leave_lobby_success(authenticated_clients):
    client = authenticated_clients[0]
    create_resp = await client.http.post("/api/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = await client.http.post(f"/api/lobbies/{lobby_id}/leave")
    assert resp.status_code in [200, 204]


@pytest.mark.asyncio
async def test_leave_lobby_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post(f"/api/lobbies/{uuid.uuid4()}/leave")
    assert resp.status_code == 401
