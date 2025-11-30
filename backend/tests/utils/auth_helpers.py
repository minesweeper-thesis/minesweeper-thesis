def register_and_login(client, email, password="pw", nickname=None):
    """Register a user, log them in, and return the current user dict."""
    if nickname is None:
        nickname = email.split("@")[0]

    payload = {
        "email": email,
        "password": password,
        "nickname": nickname,
        "settings": {},
    }

    r = client.post("/api/auth/register", json=payload)
    # allow tests to proceed if the user already exists (registration may
    # return 400/409); in that case try to login, but if credentials don't
    # match (e.g. user exists with different password) create a unique
    # fallback email to avoid test collisions when running the whole suite.
    if r.status_code not in (201,):
        assert r.status_code in (400, 409)

    r = client.post("/api/auth/login", data={"username": email, "password": password})
    if r.status_code not in (200, 204):
        # If login failed because user already exists with other credentials,
        # create a unique email and register/login with that instead so tests
        # remain isolated when run together.
        try:
            body = r.json()
        except Exception:
            body = r.text
        if isinstance(body, dict) and body.get("detail") == "LOGIN_BAD_CREDENTIALS":
            # generate a unique email by adding a short suffix
            import uuid

            local, at, domain = email.partition("@")
            unique_email = (
                f"{local}+{uuid.uuid4().hex[:8]}@{domain}"
                if at
                else f"{email}+{uuid.uuid4().hex[:8]}"
            )
            payload["email"] = unique_email
            r2 = client.post("/api/auth/register", json=payload)
            assert r2.status_code == 201
            r3 = client.post(
                "/api/auth/login", data={"username": unique_email, "password": password}
            )
            if r3.status_code not in (200, 204):
                try:
                    b2 = r3.json()
                except Exception:
                    b2 = r3.text
                raise AssertionError(
                    f"fallback login failed: status={r3.status_code}, body={b2}"
                )
            me = client.get("/api/auth/me")
            assert me.status_code == 200
            return me.json()

        # otherwise raise with context
        raise AssertionError(f"login failed: status={r.status_code}, body={body}")

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    return me.json()


def login_user(client, email, password="pw"):
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    assert r.status_code in (200, 204)
    return r
