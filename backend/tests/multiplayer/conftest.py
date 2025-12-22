from datetime import datetime, timedelta
from pprint import pprint
from typing import Annotated, Callable

import pytest
from fastapi import Depends

from backend.lib.background_handler import BackgroundRoundHandler
from backend.lib.scheduler import get_scheduler
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
        self._jobs: dict[str, tuple[datetime, Callable, tuple, dict]] = {}
        self._counter = 0
        self._delta = timedelta()

    def shutdown(self):
        self._jobs.clear()

    def schedule(self, func, when, *args, job_id=None, **kwargs):
        if job_id is None:
            job_id = f"fake-{self._counter}"
        self._counter += 1

        self._jobs[job_id] = (when + self._delta, func, args, kwargs)
        return job_id

    def cancel(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    async def skip(self, timedelta: timedelta) -> None:
        for job_id, (when, func, args, kwargs) in self._jobs.items():
            self._jobs[job_id] = (when - timedelta, func, args, kwargs)

        now = datetime.now()
        while True:
            jobs = [
                (job_id, *payload)
                for job_id, payload in self._jobs.items()
                if payload[0] <= now
            ]
            jobs.sort(key=lambda item: item[1])  # type: ignore

            pprint(jobs)

            for job_id, _when, func, args, kwargs in jobs:
                self._jobs.pop(job_id, None)
                await func(*args, **kwargs)  # type: ignore

            for job_id, (when, func, args, kwargs) in self._jobs.items():
                self._jobs[job_id] = (when - timedelta, func, args, kwargs)

            if not jobs:
                break
        self._delta -= timedelta

    def reset(self):
        self._delta = timedelta()


@pytest.fixture
def fake_scheduler():
    fake = FakeScheduler()
    api.dependency_overrides[get_scheduler] = lambda: fake
    yield fake
    api.dependency_overrides.pop(get_scheduler, None)
