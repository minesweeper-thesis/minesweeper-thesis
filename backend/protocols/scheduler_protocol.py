from datetime import datetime
from typing import Callable, Coroutine, Protocol

type JobID = str


class Scheduler(Protocol):
    def schedule(
        self,
        func: Callable[..., Coroutine],
        when: datetime,
        *args,
        job_id: JobID | None = None,
        **kwargs,
    ) -> JobID: ...

    def cancel(self, job_id: JobID) -> None: ...


__all__ = ["Scheduler", "JobID"]
