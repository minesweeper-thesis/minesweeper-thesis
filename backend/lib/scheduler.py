import asyncio
import logging
import threading
import uuid
from contextlib import suppress
from datetime import datetime
from typing import Any, Callable, Coroutine

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler

from backend.protocols import JobID, Scheduler

logger = logging.getLogger(__name__)


class AsyncScheduler(Scheduler):
    def __init__(self):
        self._scheduler: BackgroundScheduler | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._jobs: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self, loop: asyncio.AbstractEventLoop | None = None):
        if self._initialized:
            return

        if loop is None:
            loop = asyncio.get_running_loop()

        self._loop = loop
        self._scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": False,
                "max_instances": 10,
                "misfire_grace_time": 30,
            }
        )
        self._scheduler.start()
        self._initialized = True
        logger.info(f"Scheduler initialized with event loop: {loop}")

    def shutdown(self):
        if self._scheduler and self._initialized:
            try:
                self._scheduler.shutdown(wait=True)
                logger.info("Scheduler shutdown complete")
            except Exception as e:
                logger.warning(f"Scheduler shutdown warning: {e}")
            finally:
                self._initialized = False

    def schedule(
        self,
        func: Callable[..., Coroutine],
        when: datetime,
        *args,
        job_id: JobID | None = None,
        **kwargs,
    ) -> JobID:
        if not self._initialized or self._scheduler is None or self._loop is None:
            raise RuntimeError("Scheduler not initialized.")

        if job_id is None:
            job_id = str(uuid.uuid4())

        loop = self._loop

        def run_in_loop():
            try:
                future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)

                future.result(timeout=300)
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                import traceback

                traceback.print_exc()

        job = self._scheduler.add_job(
            run_in_loop,
            trigger="date",
            run_date=when,
            id=job_id,
            replace_existing=True,
        )

        with self._lock:
            self._jobs[job.id] = job

        logger.info(f"Scheduled job {job_id} for {when}")
        return job.id

    def cancel(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)

        if self._scheduler:
            with suppress(JobLookupError):
                self._scheduler.remove_job(job_id)
            logger.info(f"Cancelled job {job_id}")


_scheduler_instance: AsyncScheduler | None = None


def get_scheduler() -> Scheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AsyncScheduler()
    return _scheduler_instance


def initialize_scheduler(loop: asyncio.AbstractEventLoop | None = None):
    scheduler = get_scheduler()
    if isinstance(scheduler, AsyncScheduler):
        scheduler.initialize(loop)


def shutdown_scheduler():
    global _scheduler_instance
    if _scheduler_instance is not None:
        _scheduler_instance.shutdown()
