import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

from backend.protocols.scheduler_protocol import JobID


@dataclass
class RoundSchedule:
    countdown_to: datetime
    start_at: datetime
    end_at: datetime


class SessionRuntimeStore(Protocol):
    async def set_round_schedule(
        self,
        session_id: uuid.UUID,
        round_schedule: RoundSchedule,
    ) -> None: ...

    async def get_round_schedule(
        self, session_id: uuid.UUID
    ) -> Optional[RoundSchedule]: ...

    async def delete_round_schedule(self, session_id: uuid.UUID) -> None: ...

    async def wait_for_next_round(self, session_id: uuid.UUID) -> None: ...

    async def notify_round_ready(self, session_id: uuid.UUID) -> None: ...

    async def add_pending_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None: ...

    async def remove_pending_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None: ...

    async def is_generating(self, session_id: uuid.UUID) -> bool: ...

    async def set_lock_job_id(
        self, session_id: uuid.UUID, job_id: JobID | None
    ) -> None: ...

    async def get_lock_job_id(self, session_id: uuid.UUID) -> Optional[JobID]: ...


__all__ = ["SessionRuntimeStore"]
