import uuid
from typing import Optional

from fastapi.testclient import TestClient

from backend.tests.utils.cookies import using_auth_cookie, using_auth_cookie_sync


class AuthFixture:
    def __init__(self, test_client):
        self._client = test_client

    async def __call__(self, email="test@example.com", password="pw", nickname="test"):
        payload = {
            "email": email,
            "password": password,
            "nickname": nickname,
            "settings": {},
        }
        await self._client.post("/api/auth/register", json=payload)

        login_resp = await self._client.post(
            "/api/auth/login",
            data={"username": email, "password": password},
        )
        auth_cookie = login_resp.cookies.get("auth")
        assert auth_cookie, "Login did not set 'auth' cookie on the response"

        async with using_auth_cookie(self._client, auth_cookie):
            me_resp = await self._client.get("/api/auth/me")
        assert me_resp.status_code == 200
        user_id = me_resp.json()["id"]

        return {
            "email": email,
            "password": password,
            "nickname": nickname,
            "auth_cookie": auth_cookie,
            "user_id": user_id,
        }


class AuthFixtureSync:
    """Synchronous version of AuthFixture for TestClient (WebSocket tests)"""

    def __init__(self, test_client: TestClient):
        self._client = test_client

    def __call__(self, email="test@example.com", password="pw", nickname="test"):
        payload = {
            "email": email,
            "password": password,
            "nickname": nickname,
            "settings": {},
        }
        self._client.post("/api/auth/register", json=payload)

        login_resp = self._client.post(
            "/api/auth/login",
            data={"username": email, "password": password},
        )
        auth_cookie = login_resp.cookies.get("auth")
        assert auth_cookie, "Login did not set 'auth' cookie on the response"

        with using_auth_cookie_sync(self._client, auth_cookie):
            me_resp = self._client.get("/api/auth/me")
        assert me_resp.status_code == 200
        user_id = me_resp.json()["id"]

        return {
            "email": email,
            "password": password,
            "nickname": nickname,
            "auth_cookie": auth_cookie,
            "user_id": user_id,
        }


def register_and_authenticate(
    client: TestClient, email: str, password: str = "pw", nickname: Optional[str] = None
) -> dict:
    if nickname is None:
        nickname = email.split("@")[0]

    payload = {
        "email": email,
        "password": password,
        "nickname": nickname,
        "settings": {},
    }

    resp = client.post("/api/auth/register", json=payload)

    if resp.status_code != 201:
        unique_email = (
            f"{email.split('@')[0]}+{uuid.uuid4().hex[:8]}@{email.split('@')[1]}"
        )
        payload["email"] = unique_email
        resp = client.post("/api/auth/register", json=payload)

    login_data = {"username": email, "password": password}
    client.post("/api/auth/login", data=login_data)

    return {"email": email, "password": password, "nickname": nickname}
