import os

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82"
)


from backend.tests.utils.auth_helpers import register_and_login


def test_upload_avatar_success(client, tmp_path):
    user = register_and_login(client, "avatar@example.com")

    resp = client.post(
        "/api/avatar",
        files={"file": ("avatar.png", PNG_1X1, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "avatar_url" in data
    url = data["avatar_url"]
    assert "/img/" in url

    filename = url.split("/")[-1]
    file_path = os.path.join("img", filename)
    assert os.path.exists(file_path)

    # cleanup
    try:
        os.remove(file_path)
    except Exception:
        pass


def test_upload_avatar_invalid_file(client):
    register_and_login(client, email="inv@example.com")

    resp = client.post(
        "/api/avatar",
        files={"file": ("not_image.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 400


def test_delete_avatar_removes_file(client):
    # upload then delete
    creds = register_and_login(client, email="del@example.com")
    r = client.post(
        "/api/avatar",
        files={"file": ("avatar.png", PNG_1X1, "image/png")},
    )
    assert r.status_code == 200
    filename = r.json()["avatar_url"].split("/")[-1]
    path = os.path.join("img", filename)
    assert os.path.exists(path)

    r = client.delete("/api/avatar")
    assert r.status_code in (200, 204)
    # avatar_url in DB should be cleared
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json().get("avatar_url") is None

    # attempt cleanup of file if it still exists
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
