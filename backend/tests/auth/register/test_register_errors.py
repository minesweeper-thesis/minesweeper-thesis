import uuid

import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_register_duplicate_email_returns_400(client_no_auth):
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "secret123",
        "nickname": "first_user",
        "settings": {},
    }

    resp1 = await client_no_auth.post("/auth/register", json=payload)
    assert resp1.status_code == 201

    payload["nickname"] = "second_user"
    resp2 = await client_no_auth.post("/auth/register", json=payload)
    assert resp2.status_code == 400

    data = resp2.json()
    assert "detail" in data
    assert data["detail"] == "REGISTER_USER_ALREADY_EXISTS"


@pytest.mark.asyncio(loop_scope="session")
async def test_register_missing_required_field_returns_422(client_no_auth):
    payload = {
        "email": f"nopw-{uuid.uuid4().hex[:8]}@example.com",
        "nickname": "nopassword",
        "settings": {},
    }

    resp = await client_no_auth.post("/auth/register", json=payload)
    assert resp.status_code == 422

    data = resp.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)

    field_names = [err.get("loc", [])[-1] for err in data["detail"]]
    assert "password" in field_names


@pytest.mark.asyncio(loop_scope="session")
async def test_register_invalid_email_format_returns_422(client_no_auth):
    payload = {
        "email": "not-an-email",
        "password": "validpassword",
        "nickname": "bademail",
        "settings": {},
    }

    resp = await client_no_auth.post("/auth/register", json=payload)
    assert resp.status_code == 422
