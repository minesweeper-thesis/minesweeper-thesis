import uuid


def test_logout_clears_auth_cookie(client, auth):
    """POST /logout clears auth cookie."""
    email = f"logout-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="logoutpw", nickname="logoutuser")

    assert "auth" in client.cookies

    resp = client.post("/api/auth/logout")
    assert resp.status_code == 204
    # Cookie should be cleared or expired
    assert "auth" not in client.cookies or client.cookies.get("auth") == ""


def test_logout_without_auth_returns_401(client):
    """POST /logout without being logged in returns 401."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401
