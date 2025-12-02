import pytest

from backend.infra.pending_boards import clear_pending_boards_store
from backend.tests.utils.helpers import AuthFixture


@pytest.fixture(autouse=True)
def clear_pending_store():
    """Clear pending boards store before and after each test."""
    clear_pending_boards_store()
    yield
    clear_pending_boards_store()


@pytest.fixture
def auth(client):
    return AuthFixture(client)
