import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = _test_db_file.name
_test_db_file.close()

os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///{_test_db_path}?check_same_thread=False&timeout=30"
)
os.environ["AUTH_SECRET"] = "test-secret-key"

from backend.db import db

db.engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
db.async_session_maker = async_sessionmaker(db.engine, expire_on_commit=False)

from backend.db.db import engine, get_async_session
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
async def session():
    async with db.async_session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
async def override_dependency(session):
    async def _override():
        yield session

    app.dependency_overrides[get_async_session] = _override
    yield
    app.dependency_overrides = {}


@pytest.fixture
async def client(test_db, override_dependency):
    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://testserver"
    ) as ac:
        yield ac


@pytest.fixture
def ws_client(test_db, override_dependency):
    """Synchronous client for WebSocket tests"""
    from fastapi.testclient import TestClient

    with TestClient(app, base_url="https://testserver") as c:
        yield c


@pytest.fixture
def auth(client):
    """Async auth fixture for AsyncClient (HTTP tests)"""
    from backend.tests.utils.helpers import AuthFixture

    return AuthFixture(client)


@pytest.fixture
def auth_ws(ws_client):
    """Synchronous auth fixture for WebSocket tests"""
    from backend.tests.utils.helpers import AuthFixtureSync

    return AuthFixtureSync(ws_client)


@pytest.fixture(autouse=True)
async def clean_db(test_db):
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
