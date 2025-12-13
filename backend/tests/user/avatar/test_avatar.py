import io
import uuid

import pytest


@pytest.mark.anyio
async def test_upload_avatar_success(client, auth):
    email = f"avatar-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="avatarpw", nickname="avataruser")

    png_data = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01"
        b"\x00\x00\x00\x01"
        b"\x08\x02"
        b"\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    resp = await client.post(
        "/api/avatar",
        files={"file": ("avatar.png", io.BytesIO(png_data), "image/png")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "avatar_url" in data
    assert isinstance(data["avatar_url"], str)
    assert len(data["avatar_url"]) > 0


@pytest.mark.anyio
async def test_upload_avatar_invalid_file_type_returns_400(client, auth):
    email = f"badavatar-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="badavatarpw", nickname="badavataruser")

    resp = await client.post(
        "/api/avatar",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert "Invalid file type" in data["detail"]


@pytest.mark.anyio
async def test_upload_avatar_without_auth_returns_401(client):
    png_data = b"\x89PNG\r\n\x1a\n..."

    resp = await client.post(
        "/api/avatar",
        files={"file": ("avatar.png", io.BytesIO(png_data), "image/png")},
    )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_delete_avatar_success(client, auth):
    email = f"delavatar-{uuid.uuid4().hex[:8]}@example.com"
    await auth(email=email, password="delavatarpw", nickname="delavataruser")

    resp = await client.delete("/api/avatar")

    assert resp.status_code in [200, 204]


@pytest.mark.anyio
async def test_delete_avatar_without_auth_returns_401(client):
    resp = await client.delete("/api/avatar")
    assert resp.status_code == 401
