import asyncio
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from backend.core.game import *
from backend.repositories.exceptions import *
from backend.services.exceptions import *


class AsyncScheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        self._loop = asyncio.get_event_loop()
        self._jobs = {}
        self._lock = threading.Lock()

    def schedule(self, coro_func, when, *args, job_id=None, **kwargs):
        def runner():
            fut = asyncio.run_coroutine_threadsafe(
                coro_func(*args, **kwargs), self._loop
            )
            return fut

        job = self._scheduler.add_job(runner, "date", run_date=when, id=job_id)
        with self._lock:
            self._jobs[job.id] = job
        return job.id

    def cancel(self, job_id):
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job:
            job.remove()

    def shutdown(self):
        self._scheduler.shutdown()


async_scheduler = AsyncScheduler()
