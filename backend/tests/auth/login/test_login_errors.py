import uuid


def test_login_invalid_credentials_returns_400(client):
    email = f"badlogin-{uuid.uuid4().hex[:8]}@example.com"

    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "correctpassword",
            "nickname": "badlogintest",
            "settings": {},
        },
    )

    resp = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": "wrongpassword",
        },
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "LOGIN_BAD_CREDENTIALS"


def test_login_nonexistent_user_returns_400(client):
    """POST /login with non-existent user returns 400."""
    resp = client.post(
        "/api/auth/login",
        data={
            "username": f"noexist-{uuid.uuid4().hex[:8]}@example.com",
            "password": "anypassword",
        },
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "LOGIN_BAD_CREDENTIALS"
