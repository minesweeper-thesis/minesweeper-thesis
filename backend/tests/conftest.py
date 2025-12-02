import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Use a unique temp file for each test session
_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = _test_db_file.name
_test_db_file.close()

# SQLite with check_same_thread=False for async access and timeout
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{_test_db_path}?check_same_thread=False&timeout=30"
)

from backend.db.db import engine
from backend.main import app
from backend.repositories.orm import Base


@pytest.fixture(scope="session", autouse=True)
def test_db():
    """Database fixture - create tables once for the session."""
    import asyncio

    async def init():
        async with engine.begin() as conn:
            # Enable WAL mode for better concurrency
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=30000"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init())
    yield

    async def cleanup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(cleanup())

    try:
        os.unlink(_test_db_path)
        # Clean up WAL files too
        os.unlink(_test_db_path + "-wal")
        os.unlink(_test_db_path + "-shm")
    except:
        pass


@pytest.fixture
def client(test_db):
    with TestClient(app, base_url="https://testserver") as c:
        yield c
