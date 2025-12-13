import asyncio
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Callable, Coroutine

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

from backend.protocols import JobID, Scheduler


class AsyncScheduler(Scheduler):
    """
    Scheduler that runs async coroutines in the main FastAPI event loop.

    Uses BackgroundScheduler (runs in separate thread) but executes
    coroutines in the main asyncio event loop via run_coroutine_threadsafe.
    """

    def __init__(self):
        self._scheduler: BackgroundScheduler | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._jobs: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self, loop: asyncio.AbstractEventLoop | None = None):
        """
        Initialize the scheduler with the given event loop.
        Should be called from FastAPI lifespan when the main loop is running.
        """
        if self._initialized:
            return

        if loop is None:
            loop = asyncio.get_running_loop()

        self._loop = loop
        self._scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": False,
                "max_instances": 10,
                "misfire_grace_time": 30,  # 30 seconds grace time
            }
        )
        self._scheduler.start()
        self._initialized = True
        logger.info(f"Scheduler initialized with event loop: {loop}")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
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
        """
        Schedule an async coroutine to run at a specific time.

        Args:
            coro_func: Async function to call
            when: When to run the job
            job_id: Optional job ID (generated if not provided)
            **kwargs: Arguments to pass to coro_func

        Returns:
            Job ID
        """
        if not self._initialized or self._scheduler is None or self._loop is None:
            raise RuntimeError(
                "Scheduler not initialized. Call initialize() first, "
                "typically in FastAPI lifespan."
            )

        if job_id is None:
            job_id = str(uuid.uuid4())

        # Capture loop reference for the closure
        loop = self._loop

        def run_in_loop():
            """Run the coroutine in the main event loop."""
            try:
                future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)
                # Wait for completion and propagate any exceptions
                future.result(timeout=300)  # 5 minute timeout
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
        """Cancel a scheduled job."""
        with self._lock:
            self._jobs.pop(job_id, None)

        if self._scheduler:
            try:
                self._scheduler.remove_job(job_id)
                logger.info(f"Cancelled job {job_id}")
            except Exception:
                pass  # Job may have already run or been removed


# Global singleton
_scheduler_instance: AsyncScheduler | None = None


def get_scheduler() -> Scheduler:
    """Get the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AsyncScheduler()
    return _scheduler_instance


def initialize_scheduler(loop: asyncio.AbstractEventLoop | None = None):
    """Initialize the global scheduler. Call from FastAPI lifespan."""
    scheduler = get_scheduler()
    if isinstance(scheduler, AsyncScheduler):
        scheduler.initialize(loop)


def shutdown_scheduler():
    """Shutdown the global scheduler. Call from FastAPI lifespan."""
    global _scheduler_instance
    if _scheduler_instance is not None:
        _scheduler_instance.shutdown()
