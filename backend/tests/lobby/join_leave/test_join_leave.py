import uuid

import pytest


@pytest.mark.parametrize(
    "authenticated_clients",
    [
        [
            {
                "email": f"joinhost-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"joinhost_{uuid.uuid4().hex[:4]}",
            },
            {
                "email": f"joinguest-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "nickname": f"joinguest_{uuid.uuid4().hex[:4]}",
            },
        ]
    ],
    indirect=True,
)
@pytest.mark.asyncio(loop_scope="session")
async def test_join_lobby_returns_lobby_response(authenticated_clients):
    host_client, guest_client = authenticated_clients
    create_resp = await host_client.http.post("/lobbies")
    lobby_id = create_resp.json()["id"]

    guest_me = await guest_client.http.get("/auth/me")
    guest_id = guest_me.json()["id"]
    await host_client.http.post(
        f"/lobbies/{lobby_id}/invitations", json={"user_id": guest_id}
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_leave_lobby_success(authenticated_clients):
    client = authenticated_clients[0]
    create_resp = await client.http.post("/lobbies")
    lobby_id = create_resp.json()["id"]

    resp = await client.http.post(f"/lobbies/{lobby_id}/leave")
    assert resp.status_code in [200, 204]


@pytest.mark.asyncio(loop_scope="session")
async def test_leave_lobby_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.post(f"/lobbies/{uuid.uuid4()}/leave")
    assert resp.status_code == 401
