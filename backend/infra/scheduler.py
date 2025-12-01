import asyncio
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from backend.core.game import *
from backend.repositories.exceptions import *
from backend.services.exceptions import *
from backend.services.protocols import Scheduler


class AsyncScheduler(Scheduler):
    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        # Prefer the running loop when present; otherwise create a dedicated
        # event loop running in a background thread. This avoids DeprecationWarning
        # about `asyncio.get_event_loop()` when no loop is running.
        try:
            self._loop = asyncio.get_running_loop()
            self._own_loop_thread = None
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            self._own_loop_thread = threading.Thread(
                target=self._run_loop, name="async-scheduler-loop", daemon=True
            )
            self._own_loop_thread.start()
        self._jobs = {}
        self._lock = threading.Lock()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

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


async_scheduler = AsyncScheduler()


def get_scheduler() -> Scheduler:
    return async_scheduler
