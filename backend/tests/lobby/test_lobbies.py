import json

import backend.repositories.lobby_repo as lobby_repo
from backend.main import app
from backend.tests.utils.auth_helpers import register_and_login


def setup_function():
    # clear in-memory lobby state between test runs
    lobby_repo.lobbies.clear()
    lobby_repo.invitations.clear()
    lobby_repo.messages.clear()


def test_lobby_full_flow(client):
    # create two independent TestClient instances representing host and guest
    from fastapi.testclient import TestClient as _TC

    with (
        _TC(app, base_url="https://testserver") as host_client,
        _TC(app, base_url="https://testserver") as guest_client,
    ):
        # register and login both users on their clients
        host = register_and_login(host_client, "host@example.com", nickname="host")
        guest = register_and_login(guest_client, "guest@example.com", nickname="guest")

        # open websocket connections and consume initial current_lobby messages
        host_auth = host_client.cookies.get("auth")
        guest_auth = guest_client.cookies.get("auth")

        host_headers = {"cookie": f"auth={host_auth}"} if host_auth else {}
        guest_headers = {"cookie": f"auth={guest_auth}"} if guest_auth else {}

        with (
            host_client.websocket_connect("/api/ws", headers=host_headers) as host_ws,
            guest_client.websocket_connect(
                "/api/ws", headers=guest_headers
            ) as guest_ws,
        ):
            # initial welcome/current lobby messages
            _ = host_ws.receive_text()
            _ = guest_ws.receive_text()

            # host creates a lobby
            r = host_client.post("/api/lobbies")
            assert r.status_code == 200
            lobby = r.json()
            assert "id" in lobby
            lobby_id = lobby["id"]

            # update lobby config (host)
            cfg = {
                "rounds": 2,
                "max_round_time": 30,
                "difficulty_level": {"rows": 3, "columns": 3, "mine_count": 2},
                "game_mode": "normal",
                "generator_type": "random",
            }
            r = host_client.put(f"/api/lobbies/{lobby_id}", json=cfg)
            assert r.status_code in (200, 204)

            # host invites guest
            r = host_client.post(
                f"/api/lobbies/{lobby_id}/invitations", json={"user_id": guest["id"]}
            )
            assert r.status_code in (200, 204)

            # guest websocket should receive an invitation notification
            inv_msg = guest_ws.receive_text()
            parsed_inv = json.loads(inv_msg)
            assert parsed_inv.get("type") == "invitation"
            assert str(parsed_inv.get("lobby", {}).get("id")) == lobby_id

            # find created invitation id in repo
            inv_id = None
            for inv in lobby_repo.invitations.values():
                if str(inv.invitee.id) == guest["id"]:
                    inv_id = inv.id
                    break
            assert inv_id is not None

            # guest joins using invitation (guest_client)
            r = guest_client.post(
                f"/api/lobbies/{lobby_id}/join", json={"invitation_id": str(inv_id)}
            )
            assert r.status_code == 200
            body = r.json()
            assert "id" in body and body["id"] == lobby_id

            # host websocket should receive invitation_response and user_connection notifications
            types = set()
            host_notifications = []
            # read up to 3 messages that should arrive after the join
            for _ in range(3):
                n = json.loads(host_ws.receive_text())
                host_notifications.append(n)
                types.add(n.get("type"))
                if "invitation_response" in types and "user_connection" in types:
                    break
            assert "invitation_response" in types
            assert "user_connection_status" in types

            # guest sends chat message
            msg = {"content": "hello from guest"}
            r = guest_client.post(f"/api/lobbies/{lobby_id}/chat-messages", json=msg)
            assert r.status_code in (200, 204)

            # both host and guest should receive chat_message notifications
            def receive_until_type(ws, expected_type, tries=4):
                for _ in range(tries):
                    msg = json.loads(ws.receive_text())
                    if msg.get("type") == expected_type:
                        return msg
                raise AssertionError(
                    f"Did not receive {expected_type} after {tries} tries"
                )

            guest_chat = receive_until_type(guest_ws, "chat_message")
            host_chat = receive_until_type(host_ws, "chat_message")
            assert guest_chat.get("type") == "chat_message"
            assert host_chat.get("type") == "chat_message"

            # guest leaves
            r = guest_client.post(f"/api/lobbies/{lobby_id}/leave")
            assert r.status_code in (200, 204)

            # host invites another user then reject flow
            with _TC(app, base_url="https://testserver") as other_client:
                other = register_and_login(
                    other_client, "other@example.com", nickname="other"
                )
                r = host_client.post(
                    f"/api/lobbies/{lobby_id}/invitations",
                    json={"user_id": other["id"]},
                )
                assert r.status_code in (200, 204)

                # find invitation for other
                other_inv = None
                for inv in lobby_repo.invitations.values():
                    if str(inv.invitee.id) == other["id"]:
                        other_inv = inv.id
                        break
                assert other_inv is not None

                # other rejects the invitation (ensure other_client is used)
                r = other_client.delete(f"/api/invitations/{other_inv}")
                assert r.status_code in (200, 204)
