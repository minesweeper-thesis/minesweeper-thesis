import pytest

from backend.tests.utils.helpers import AuthFixture


@pytest.fixture
def auth(client):
    return AuthFixture(client)
