import uuid
from typing import Optional

from fastapi.testclient import TestClient


class AuthFixture:
    """Wspólny fixture do rejestracji i logowania w testach"""

    def __init__(self, test_client):
        self._client = test_client

    def __call__(self, email="test@example.com", password="pw", nickname="test"):
        payload = {
            "email": email,
            "password": password,
            "nickname": nickname,
            "settings": {},
        }
        self._client.post("/api/auth/register", json=payload)
        self._client.post(
            "/api/auth/login", data={"username": email, "password": password}
        )
        return {"email": email, "password": password, "nickname": nickname}


def register_and_authenticate(
    client: TestClient,
    email: str,
    password: str = "pw",
    nickname: Optional[str] = None,
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
