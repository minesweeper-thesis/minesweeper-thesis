import pytest

from typing import Annotated

from fastapi import Depends

from backend.lib.background_handler import BackgroundRoundHandler
from backend.services.multi.round_scheduler import RoundScheduler
from backend.main import api


@pytest.fixture
def background_handler_override():
    class TestBackgroundRoundHandler:
        def __init__(self, round_scheduler: Annotated[RoundScheduler, Depends()]):
            self.round_scheduler = round_scheduler

        async def on_board_generated(self, session_id, generation_id, board):
            await self.round_scheduler.on_board_generated(
                session_id, generation_id, board
            )

    api.dependency_overrides[BackgroundRoundHandler] = TestBackgroundRoundHandler
    yield
    api.dependency_overrides.pop(BackgroundRoundHandler, None)


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


@pytest.fixture
def fake_scheduler(monkeypatch):
    import backend.lib.scheduler as scheduler_module

    fake = FakeScheduler()
    monkeypatch.setattr(scheduler_module, "_scheduler_instance", fake)
    return fake
