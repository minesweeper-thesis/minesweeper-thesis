from typing import Annotated

import pytest
from fastapi import Depends

from backend.lib.background_handler import BackgroundRoundHandler
from backend.main import api
from backend.services.multi.round_scheduler import RoundScheduler


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

    def shutdown(self):
        self._jobs.clear()

    def schedule(self, func, when, *args, job_id=None, **kwargs):
        if job_id is None:
            job_id = f"fake-{self._counter}"
        self._counter += 1

        self._jobs[job_id] = (when, func, args, kwargs)
        return job_id

    def cancel(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    async def run_matching(self, names: set[str]) -> None:
        jobs = [
            (job_id, *payload)
            for job_id, payload in self._jobs.items()
            if getattr(payload[1], "__name__", "") in names
        ]
        jobs.sort(key=lambda item: item[1])

        for job_id, _when, func, args, kwargs in jobs:
            self._jobs.pop(job_id, None)
            await func(*args, **kwargs)

    async def run_all(self) -> None:
        jobs = [(job_id, *payload) for job_id, payload in self._jobs.items()]
        jobs.sort(key=lambda item: item[1])

        for job_id, _when, func, args, kwargs in jobs:
            self._jobs.pop(job_id, None)
            await func(*args, **kwargs)


@pytest.fixture
def fake_scheduler(monkeypatch):
    import backend.lib.scheduler as scheduler_module

    fake = FakeScheduler()
    monkeypatch.setattr(scheduler_module, "_scheduler_instance", fake)
    return fake
