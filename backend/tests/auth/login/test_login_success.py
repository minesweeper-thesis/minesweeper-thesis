
import uuid

import pytest

from backend.schemas.user import CurrentUserResponse


@pytest.mark.asyncio
async def test_login_success_sets_auth_cookie_and_me_returns_user(client):
	email = f"login-{uuid.uuid4().hex[:8]}@example.com"

	await client.post(
		"/api/auth/register",
		json={
			"email": email,
			"password": "mypassword",
			"nickname": "logintest",
			"settings": {},
		},
	)

	resp = await client.post(
		"/api/auth/login",
		data={
			"username": email,
			"password": "mypassword",
		},
	)

	assert resp.status_code == 204 or resp.status_code == 200
	assert "auth" in client.cookies

	me_resp = await client.get("/api/auth/me")
	assert me_resp.status_code == 200
	user = CurrentUserResponse(**me_resp.json())
	assert user.email == email
	assert user.id is not None

