import uuid
from typing import Callable, Protocol

type JobID = uuid.UUID


class Scheduler(Protocol):
    def schedule(self, func: Callable, when, **kwargs) -> JobID: ...

    def cancel(self, job_id: JobID) -> None: ...


__all__ = ["Scheduler"]
