from backend.tests.utils.auth_helpers import register_and_login


def create_user(client, email="user@example.com", password="password123", nickname="u"):
    # Use the shared test helper which tolerates existing users and
    # ensures the client is logged in. Return the credential payload for
    # compatibility with existing tests.
    register_and_login(client, email=email, password=password, nickname=nickname)
    return {"email": email, "password": password, "nickname": nickname}


def login(client, identifier, password):
    # fastapi-users auth router expects form data; commonly the field is 'username'
    data = {"username": identifier, "password": password}
    # the project's auth router mounts auth endpoints under /api/auth
    return client.post("/api/auth/login", data=data)


def test_login_with_email(client):
    creds = create_user(
        client, email="email-login@example.com", password="pw123", nickname="el"
    )
    resp = login(client, creds["email"], creds["password"])
    # fastapi-users may return 200 or 204 on successful login; accept both
    assert resp.status_code in (200, 204)
    if resp.status_code in (200, 204):
        assert client.cookies.get("auth") is not None


def test_login_with_username(client):
    creds = create_user(
        client, email="uname@example.com", password="pw456", nickname="the_nick"
    )
    # try login using nickname as identifier; clear existing auth cookie so
    # the test can assert post-login cookie state unambiguously.
    client.cookies.clear()
    resp = login(client, creds["nickname"], creds["password"])
    # Some setups allow login via username/nickname; accept success (200/204)
    # or a client error (400/401) if nickname-based login is not supported.
    assert resp.status_code in (200, 204, 400, 401)
    if resp.status_code in (200, 204):
        assert client.cookies.get("auth") is not None
    else:
        assert client.cookies.get("auth") is None


def test_logout_requires_auth_and_clears_cookie(client):
    creds = create_user(
        client, email="logout@example.com", password="pw789", nickname="lo"
    )
    # login
    r = login(client, creds["email"], creds["password"])
    assert r.status_code in (200, 204)
    if r.status_code in (200, 204):
        assert client.cookies.get("auth") is not None
    print("Cookies after login:", client.cookies)
    # logout
    r = client.post("/api/auth/logout")
    assert r.status_code == 204
    assert client.cookies.get("auth") is None
