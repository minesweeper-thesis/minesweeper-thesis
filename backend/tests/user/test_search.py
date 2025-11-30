from backend.tests.utils.auth_helpers import register_and_login


def test_search_users(client):
    alice = register_and_login(client, "alice@example.com", nickname="alice")
    bob = register_and_login(client, "bob@example.com", nickname="bobby")
    charlie = register_and_login(client, "charlie@example.com", nickname="char")

    # perform search for 'ali' should find alice first
    resp = client.get("/api/search?query=ali")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    items = data["items"]
    assert any(item["nickname"] == "alice" for item in items)
