import uuid

from backend.tests.utils.auth_helpers import register_and_login


def test_register_success(client):
    # Use the shared helper so the test is resilient to pre-existing state
    email = f"alice+{uuid.uuid4().hex}@example.com"
    user = register_and_login(
        client, email=email, password="strongpassword123", nickname="alice"
    )
    assert user["email"] == email
    assert user["nickname"] == "alice"
    assert "id" in user


def test_register_duplicate_email(client):
    payload = {
        "email": "bob@example.com",
        "password": "secret123",
        "nickname": "bob",
        "settings": {},
    }
    # Ensure the first registration succeeds (use helper to tolerate existing state)
    register_and_login(
        client,
        email=payload["email"],
        password=payload["password"],
        nickname=payload["nickname"],
    )
    r2 = client.post("/api/auth/register", json=payload)
    assert 400 <= r2.status_code < 500


def test_register_missing_password(client):
    payload = {"email": "no-pass@example.com", "nickname": "nopass", "settings": {}}
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 422
