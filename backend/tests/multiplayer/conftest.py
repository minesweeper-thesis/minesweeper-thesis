import pytest
from fastapi.testclient import TestClient

from backend.main import api, app
from backend.tests.utils.helpers import AuthFixture, AuthFixtureSync


class ImmediateBoardGenerator:
    def __init__(self):
        self._statuses = {}

    async def generate_board(self, settings, on_completed):
        import random
        import uuid

        from backend.core.board import Board

        generation_id = uuid.uuid4()
        self._statuses[generation_id] = "completed"

        rows = settings.difficulty_level.rows
        cols = settings.difficulty_level.columns
        mines = settings.difficulty_level.mine_count

        start_field = (0, 0)
        cells = [
            (i, j) for i in range(rows) for j in range(cols) if (i, j) != start_field
        ]
        rng = random.Random(int.from_bytes(generation_id.bytes, "big"))
        minefields = rng.sample(cells, k=mines)

        board = Board(
            id=uuid.uuid4(),
            minefields=minefields,
            start_field=start_field,
            generation_settings=settings,
        )
        await on_completed(generation_id, board)
        return generation_id

    async def get_generation_status(self, generation_id):
        return self._statuses.get(generation_id, "completed")


class FakeScheduler:
    def __init__(self):
        self._jobs: dict[str, tuple[object, object, tuple, dict]] = {}
        self._counter = 0
        self._loop = None

    def shutdown(self):
        self._jobs.clear()

    def schedule(self, func, when, *args, job_id=None, **kwargs):
        import asyncio

        if job_id is None:
            job_id = f"fake-{self._counter}"
        self._counter += 1

        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = None

        self._jobs[job_id] = (when, func, args, kwargs)
        return job_id

    def cancel(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    def run_matching(self, names: set[str]) -> None:
        import asyncio

        if self._loop is None:
            raise RuntimeError("FakeScheduler loop not set yet")

        async def _run():
            jobs = [
                (job_id, *payload)
                for job_id, payload in self._jobs.items()
                if getattr(payload[1], "__name__", "") in names
            ]
            jobs.sort(key=lambda item: item[1])

            for job_id, _when, func, args, kwargs in jobs:
                self._jobs.pop(job_id, None)
                await func(*args, **kwargs)

        asyncio.run_coroutine_threadsafe(_run(), self._loop).result(timeout=10)

    def run_all(self) -> None:
        import asyncio

        if self._loop is None:
            raise RuntimeError("FakeScheduler loop not set yet")

        async def _run():
            jobs = [(job_id, *payload) for job_id, payload in self._jobs.items()]
            jobs.sort(key=lambda item: item[1])
            for job_id, _when, func, args, kwargs in jobs:
                self._jobs.pop(job_id, None)
                await func(*args, **kwargs)

        asyncio.run_coroutine_threadsafe(_run(), self._loop).result(timeout=10)


@pytest.fixture(scope="session")
def board_generator_override():
    from backend.lib.board_generator import LocalBoardGenerator

    generator = ImmediateBoardGenerator()

    def _override():
        return generator

    api.dependency_overrides[LocalBoardGenerator] = _override
    yield
    api.dependency_overrides.pop(LocalBoardGenerator, None)


@pytest.fixture
async def client(test_db, board_generator_override):
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://testserver"
    ) as ac:
        yield ac


@pytest.fixture
def auth(client):
    return AuthFixture(client)


@pytest.fixture
def ws_client(test_db):
    """Synchronous client for WebSocket tests"""
    with TestClient(app, base_url="https://testserver") as c:
        yield c


@pytest.fixture
def auth_ws(ws_client):
    """Synchronous auth fixture for WebSocket tests"""
    return AuthFixtureSync(ws_client)


@pytest.fixture
def fake_scheduler(monkeypatch):
    fake = FakeScheduler()

    import backend.lib.scheduler as scheduler_module

    monkeypatch.setattr(scheduler_module, "_scheduler_instance", fake)
    return fake
