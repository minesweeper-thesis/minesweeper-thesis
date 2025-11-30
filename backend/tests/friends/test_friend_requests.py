import json

from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.utils.auth_helpers import login_user, register_and_login


def register_user(client, email, password="pw", nickname=None):
    # wrapper around shared helper
    return register_and_login(client, email, password, nickname)


def login(client, email, password="pw"):
    return login_user(client, email, password)


def test_friend_request_flow(client):
    # Create independent clients for A (inviter) and B (invitee)
    import uuid as _uuid

    # unique emails to avoid collisions with other tests
    a_email = f"a+{_uuid.uuid4().hex}@example.com"
    b_email = f"b+{_uuid.uuid4().hex}@example.com"

    with (
        TestClient(app, base_url="https://testserver") as a_client,
        TestClient(app, base_url="https://testserver") as b_client,
    ):
        a = register_user(a_client, a_email, nickname="a")
        b = register_user(b_client, b_email, nickname="b")

        # open websocket for B to capture notifications (pass auth cookie explicitly)
        b_auth = b_client.cookies.get("auth")
        b_headers = {"cookie": f"auth={b_auth}"} if b_auth else {}
        with b_client.websocket_connect("/api/ws", headers=b_headers) as b_ws:
            # consume initial current_lobby message
            _ = b_ws.receive_text()

            login(a_client, a_email)
            payload = {"friend_id": b["id"]}
            r = a_client.post("/api/friend-requests", json=payload)
            if r.status_code != 200:
                print("friend request response:", r.status_code, r.text)
            assert r.status_code == 200

            fr = r.json()
            assert fr["friend"]["id"] == b["id"]

            # B should receive websocket notification about the friend request
            notif = json.loads(b_ws.receive_text())
            assert notif.get("type") == "friend_request"
            assert str(notif.get("id")) == fr["id"]

    # Check sent requests as A (use same client but authenticate as A)
    login(client, a_email)
    r = client.get("/api/friend-requests/sent")
    assert r.status_code == 200
    sent = r.json()
    assert any(item["id"] == fr["id"] for item in sent.get("items", []))

    # Login as B and see pending requests
    login(client, b_email)
    r = client.get("/api/friend-requests/pending")
    assert r.status_code == 200
    pending = r.json()
    assert any(item["id"] == fr["id"] for item in pending.get("items", []))

    # Accept the friend request as B
    r = client.post(f"/api/friend-requests/{fr['id']}/accept")
    assert r.status_code in (200, 204)

    # After accept, the original sender (A) should see the request marked accepted
    login(client, a_email)
    r = client.get("/api/friend-requests/sent")
    assert r.status_code == 200
    sent_after = r.json()
    # After acceptance the request is no longer pending for the sender
    assert not any(item.get("id") == fr["id"] for item in sent_after.get("items", []))

    # Check friends list while logged in as B
    login(client, b_email)
    r = client.get("/api/friends")
    assert r.status_code == 200
    friends_page = r.json()
    assert any(item["id"] == a["id"] for item in friends_page.get("items", []))

    # Remove friendship as B
    r = client.delete(f"/api/friends/{a['id']}")
    assert r.status_code in (200, 204)


def test_reject_friend_request_flow(client):
    # Create users C and D for rejection flow
    with (
        TestClient(app, base_url="https://testserver") as c_client,
        TestClient(app, base_url="https://testserver") as d_client,
    ):
        c = register_user(c_client, "c@example.com", nickname="c")
        d = register_user(d_client, "d@example.com", nickname="d")

        # C sends request to D
        login(c_client, "c@example.com")
        payload = {"friend_id": d["id"]}
        r = c_client.post("/api/friend-requests", json=payload)
        assert r.status_code == 200
        fr = r.json()

        # D rejects the request
        login(d_client, "d@example.com")
        r = d_client.post(f"/api/friend-requests/{fr['id']}/reject")
        assert r.status_code in (200, 204)

        # Verify pending lists do not include the request
        login(c_client, "c@example.com")
        r = c_client.get("/api/friend-requests/sent")
        assert r.status_code == 200
        assert not any(item.get("id") == fr["id"] for item in r.json().get("items", []))

        login(d_client, "d@example.com")
        r = d_client.get("/api/friend-requests/pending")
        assert r.status_code == 200
        assert not any(item.get("id") == fr["id"] for item in r.json().get("items", []))
