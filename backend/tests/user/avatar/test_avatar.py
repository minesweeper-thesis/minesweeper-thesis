import io
from urllib.parse import urlparse

import pytest

TEST_AVATAR = (
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


@pytest.mark.asyncio(loop_scope="session")
async def test_upload_avatar_success(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.http.post(
        "/avatar",
        files={"file": ("avatar.png", io.BytesIO(TEST_AVATAR), "image/png")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "avatar_url" in data
    urlparsed = urlparse(data["avatar_url"])
    assert urlparsed.scheme in ("http", "https")
    assert urlparsed.netloc != ""
    assert urlparsed.path != ""


@pytest.mark.asyncio(loop_scope="session")
async def test_upload_avatar_invalid_file_type_returns_400(authenticated_clients):
    client = authenticated_clients[0]
    resp = await client.http.post(
        "/avatar",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert "Invalid file type" in data["detail"]


@pytest.mark.asyncio(loop_scope="session")
async def test_upload_avatar_without_auth_returns_401(client_no_auth):
    png_data = b"\x89PNG\r\n\x1a\n..."

    resp = await client_no_auth.post(
        "/avatar",
        files={"file": ("avatar.png", io.BytesIO(png_data), "image/png")},
    )

    assert resp.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_avatar_success(authenticated_clients):
    client = authenticated_clients[0]
    await client.http.post(
        "/avatar",
        files={"file": ("avatar.png", io.BytesIO(TEST_AVATAR), "image/png")},
    )
    me = await client.http.get("/auth/me")
    assert me.status_code == 200
    data = me.json()
    assert data.get("avatar_url") is not None

    resp = await client.http.delete("/avatar")

    assert resp.status_code == 200

    me = await client.http.get("/auth/me")
    assert me.status_code == 200
    data = me.json()
    assert data.get("avatar_url") is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_avatar_without_auth_returns_401(client_no_auth):
    resp = await client_no_auth.delete("/avatar")
    assert resp.status_code == 401
