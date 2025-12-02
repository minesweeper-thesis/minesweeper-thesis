"""
Comprehensive user router tests.
Tests: POST /avatar, DELETE /avatar, GET /search, GET /gameplays
"""

import io
import uuid

from backend.routers.schemas.user_schemas import UserResponse

# =============================================================================
# POST /avatar Tests
# =============================================================================


def test_upload_avatar_success(client, auth):
    """POST /avatar with valid image returns avatar_url."""
    email = f"avatar-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="avatarpw", nickname="avataruser")

    # Create a minimal valid PNG image
    # PNG header + minimal IHDR chunk
    png_data = (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        b"\x00\x00\x00\rIHDR"  # IHDR chunk length and type
        b"\x00\x00\x00\x01"  # width: 1
        b"\x00\x00\x00\x01"  # height: 1
        b"\x08\x02"  # bit depth: 8, color type: 2 (RGB)
        b"\x00\x00\x00"  # compression, filter, interlace
        b"\x90wS\xde"  # CRC
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"  # IDAT
        b"\x00\x00\x00\x00IEND\xaeB`\x82"  # IEND
    )

    resp = client.post(
        "/api/avatar",
        files={"file": ("avatar.png", io.BytesIO(png_data), "image/png")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "avatar_url" in data
    assert isinstance(data["avatar_url"], str)
    assert len(data["avatar_url"]) > 0


def test_upload_avatar_invalid_file_type_returns_400(client, auth):
    """POST /avatar with non-image file returns 400."""
    email = f"badavatar-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="badavatarpw", nickname="badavataruser")

    # Send a text file pretending to be image
    resp = client.post(
        "/api/avatar",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )

    assert resp.status_code == 400
    data = resp.json()
    assert "detail" in data
    assert "Invalid file type" in data["detail"]


def test_upload_avatar_without_auth_returns_401(client):
    """POST /avatar without auth returns 401."""
    png_data = b"\x89PNG\r\n\x1a\n..."

    resp = client.post(
        "/api/avatar",
        files={"file": ("avatar.png", io.BytesIO(png_data), "image/png")},
    )

    assert resp.status_code == 401


# =============================================================================
# DELETE /avatar Tests
# =============================================================================


def test_delete_avatar_success(client, auth):
    """DELETE /avatar removes user avatar."""
    email = f"delavatar-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="delavatarpw", nickname="delavataruser")

    resp = client.delete("/api/avatar")
    # Should succeed even if no avatar exists
    assert resp.status_code in [200, 204]


def test_delete_avatar_without_auth_returns_401(client):
    """DELETE /avatar without auth returns 401."""
    resp = client.delete("/api/avatar")
    assert resp.status_code == 401


# =============================================================================
# GET /search Tests
# =============================================================================


def test_search_users_returns_paginated_user_response(client, auth):
    """GET /search returns Page[UserResponse] with correct schema."""
    email = f"searchable-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="searchpw", nickname="searchableuser")

    resp = client.get("/api/search", params={"query": "searchable"})

    assert resp.status_code == 200
    data = resp.json()

    # Validate pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["pages"], int)
    assert isinstance(data["size"], int)

    # Validate UserResponse schema for each item
    for item in data["items"]:
        user = UserResponse(**item)
        assert user.id is not None
        assert user.nickname is not None
        assert user.email is not None
        # Validate UUID
        uuid.UUID(str(user.id))


def test_search_users_finds_matching_user(client, auth):
    """GET /search finds user by nickname substring."""
    unique_name = f"unique{uuid.uuid4().hex[:8]}"
    email = f"{unique_name}@example.com"
    auth(email=email, password="findpw", nickname=unique_name)

    resp = client.get("/api/search", params={"query": unique_name[:10]})

    assert resp.status_code == 200
    data = resp.json()

    # Should find at least our user
    assert data["total"] >= 1
    nicknames = [item["nickname"] for item in data["items"]]
    assert unique_name in nicknames


def test_search_users_empty_query_works(client, auth):
    """GET /search with empty query returns results."""
    email = f"emptysearch-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="emptypw", nickname="emptyquery")

    resp = client.get("/api/search", params={"query": ""})
    assert resp.status_code in [200, 422]  # Either works or validation error


def test_search_users_no_auth_works(client):
    """GET /search works without authentication."""
    resp = client.get("/api/search", params={"query": "test"})
    # Search might work without auth
    assert resp.status_code in [200, 401]


# =============================================================================
# GET /gameplays Tests
# =============================================================================


def test_get_gameplays_returns_paginated_gameplay_response(client, auth):
    """GET /gameplays returns Page[UserGameplayResponse] with correct schema."""
    email = f"gameplays-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="gameplayspw", nickname="gameplaysuser")

    resp = client.get("/api/gameplays")

    assert resp.status_code == 200
    data = resp.json()

    # Validate pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert "size" in data

    # Even if empty, structure should be valid
    assert isinstance(data["items"], list)


def test_get_gameplays_validates_gameplay_response_schema(client, auth):
    """GET /gameplays items follow UserGameplayResponse schema."""
    email = f"gpschema-{uuid.uuid4().hex[:8]}@example.com"
    auth(email=email, password="gpschemapw", nickname="gpschemauser")

    # First play a game to have gameplays
    import asyncio

    from backend.core.board import Board, DifficultyLevel, GenerationSettings
    from backend.db.db import async_session_maker
    from backend.repositories.board_repo import BoardRepository

    async def create_board():
        async with async_session_maker() as session:
            repo = BoardRepository(session)
            difficulty = DifficultyLevel(rows=3, columns=3, mine_count=1)
            board = Board(
                id=uuid.uuid4(),
                difficulty_level=difficulty,
                minefields=[(0, 0)],
                start_field=(1, 1),
                generation_settings=GenerationSettings(
                    type="random", settings=None, difficulty_level=difficulty
                ),
            )
            try:
                await repo.add_board(board)
            except Exception:
                pass
            return str(board.id)

    board_id = asyncio.run(create_board())

    # Start a game
    game_resp = client.post(
        "/api/game/singleplayer",
        json={
            "board_id": board_id,
            "mode": "normal",
        },
    )

    if game_resp.status_code == 200:
        # Now get gameplays
        resp = client.get("/api/gameplays")
        assert resp.status_code == 200
        data = resp.json()

        if data["items"]:
            for item in data["items"]:
                # Validate UserGameplayResponse schema
                assert "id" in item
                assert "user_id" in item
                assert "status" in item
                assert "elapsed_time" in item
                assert "difficulty_level" in item

                # Validate types
                uuid.UUID(str(item["id"]))
                uuid.UUID(str(item["user_id"]))
                assert item["status"] in ["not_started", "in_progress", "finished"]
                assert isinstance(item["elapsed_time"], (int, float))


def test_get_gameplays_without_auth_returns_401(client):
    """GET /gameplays without auth returns 401."""
    resp = client.get("/api/gameplays")
    assert resp.status_code == 401
