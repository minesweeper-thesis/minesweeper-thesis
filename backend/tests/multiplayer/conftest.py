from datetime import datetime
from typing import Callable

import pytest

from backend.lib.scheduler import get_scheduler
from backend.main import api


class FakeScheduler:
    def __init__(self, time_machine):
        self._jobs: dict[str, tuple[datetime, Callable, tuple, dict]] = {}
        self._time_machine = time_machine

    def shutdown(self):
        self._jobs.clear()

    def schedule(self, func, when, *args, job_id=None, **kwargs):
        if job_id is None:
            job_id = f"fake-{len(self._jobs)}"

        self._jobs[job_id] = (when, func, args, kwargs)

        return job_id

    def cancel(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    async def skip(self, timedelta) -> None:
        self._time_machine.shift(timedelta)
        while True:
            now = datetime.now()

            due_jobs = [
                (job_id, payload)
                for job_id, payload in self._jobs.items()
                if payload[0] <= now
            ]

            if not due_jobs:
                break

            due_jobs.sort(key=lambda item: item[1][0])

            for job_id, (when, func, args, kwargs) in due_jobs:
                self._jobs.pop(job_id, None)
                await func(*args, **kwargs)


@pytest.fixture
def fake_scheduler(time_machine):
    fake = FakeScheduler(time_machine)
    api.dependency_overrides[get_scheduler] = lambda: fake
    yield fake
    api.dependency_overrides.pop(get_scheduler, None)
