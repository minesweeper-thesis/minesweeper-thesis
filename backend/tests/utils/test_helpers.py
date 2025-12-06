from fastapi.testclient import TestClient

from backend.main import app


def create_second_user_and_login(email, password, nickname):
    client = TestClient(app, base_url="https://testserver")
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "nickname": nickname,
            "settings": {},
        },
    )
    client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )
    return client
