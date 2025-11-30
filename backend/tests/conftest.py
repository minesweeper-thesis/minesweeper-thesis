import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def test_db():
    """Set DATABASE_URL to a shared test DB file `backend/tests/test.db`.

    This fixture runs once per test session and ensures the env var is set
    before the app is imported by tests. It also removes the DB file after
    the session.
    """
    db_path = Path(__file__).parent / "test.db"
    url = f"sqlite+aiosqlite:///{db_path}"
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url

    # Ensure a clean DB at start
    try:
        if db_path.exists():
            db_path.unlink()
    except Exception:
        pass

    yield db_path

    # Cleanup after all tests
    try:
        if db_path.exists():
            db_path.unlink()
    except Exception:
        pass

    # restore env
    if prev is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = prev


@pytest.fixture
def client(test_db):
    # Import app after DATABASE_URL is configured by test_db
    from fastapi.testclient import TestClient

    from backend.main import app

    # Use https base_url so cookies with the `Secure` attribute are sent by
    # TestClient. fastapi-users sets cookies as Secure, so using http causes
    # the test client to omit them and authentication fails.
    with TestClient(app, base_url="https://testserver") as c:
        yield c
