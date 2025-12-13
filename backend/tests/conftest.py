import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = _test_db_file.name
_test_db_file.close()

os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{_test_db_path}?check_same_thread=False&timeout=30"
)
os.environ["AUTH_SECRET"] = "test-secret-key"

from backend.db.db import engine
from backend.main import app
from backend.repositories.orm import Base


@pytest.fixture(scope="session", autouse=True)
async def test_db():
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA busy_timeout=30000"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    try:
        os.unlink(_test_db_path)
        os.unlink(_test_db_path + "-wal")
        os.unlink(_test_db_path + "-shm")
    except:
        pass


@pytest.fixture
async def client(test_db):
    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://testserver"
    ) as ac:
        yield ac


@pytest.fixture
def ws_client(test_db):
    """Synchronous client for WebSocket tests"""
    from fastapi.testclient import TestClient

    with TestClient(app, base_url="https://testserver") as c:
        yield c


@pytest.fixture
def auth_ws(ws_client):
    """Synchronous auth fixture for WebSocket tests"""
    from backend.tests.utils.helpers import AuthFixtureSync

    return AuthFixtureSync(ws_client)
