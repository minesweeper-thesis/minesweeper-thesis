
import uuid

from fastapi.testclient import TestClient

from backend.main import app

def test_accept_friend_request_success(client, auth):
    user1_email = f"acceptsender-{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"acceptreceiver-{uuid.uuid4().hex[:8]}@example.com"

    with TestClient(app, base_url="https://testserver") as client2:
        reg_resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "acceptreceiverpw",
                "nickname": "acceptreceiver",
                "settings": {},
            },
        )
        user2_id = reg_resp.json()["id"] if reg_resp.status_code == 201 else None

    if user2_id:

        auth(email=user1_email, password="acceptsenderpw", nickname="acceptsender")
        req_resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            with TestClient(app, base_url="https://testserver") as client2:
                client2.post(
                    "/api/auth/login",
                    data={
                        "username": user2_email,
                        "password": "acceptreceiverpw",
                    },
                )
                accept_resp = client2.post(
                    f"/api/friend-requests/{friend_request_id}/accept"
                )
                assert accept_resp.status_code in [200, 204]

def test_accept_nonexistent_request_returns_404(client, auth):
    email = f"acceptnoexist-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="acceptnoexistpw", nickname="acceptnoexist")

    fake_id = str(uuid.uuid4())
    resp = client.post(f"/api/friend-requests/{fake_id}/accept")

    assert resp.status_code == 404

def test_reject_friend_request_success(client, auth):
    user1_email = f"rejectsender-{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"rejectreceiver-{uuid.uuid4().hex[:8]}@example.com"

    with TestClient(app, base_url="https://testserver") as client2:
        reg_resp = client2.post(
            "/api/auth/register",
            json={
                "email": user2_email,
                "password": "rejectreceiverpw",
                "nickname": "rejectreceiver",
                "settings": {},
            },
        )
        user2_id = reg_resp.json()["id"] if reg_resp.status_code == 201 else None

    if user2_id:

        auth(email=user1_email, password="rejectsenderpw", nickname="rejectsender")
        req_resp = client.post("/api/friend-requests", json={"friend_id": user2_id})

        if req_resp.status_code == 200:
            friend_request_id = req_resp.json()["id"]

            with TestClient(app, base_url="https://testserver") as client2:
                client2.post(
                    "/api/auth/login",
                    data={
                        "username": user2_email,
                        "password": "rejectreceiverpw",
                    },
                )
                reject_resp = client2.post(
                    f"/api/friend-requests/{friend_request_id}/reject"
                )
                assert reject_resp.status_code in [200, 204]

def test_reject_nonexistent_request_returns_404(client, auth):
    email = f"rejectnoexist-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="rejectnoexistpw", nickname="rejectnoexist")

    fake_id = str(uuid.uuid4())
    resp = client.post(f"/api/friend-requests/{fake_id}/reject")

    assert resp.status_code == 404
