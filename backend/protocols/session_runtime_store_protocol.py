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
        ttl: int,
    ) -> None: ...

    async def get_round_schedule(
        self, session_id: uuid.UUID
    ) -> Optional[RoundSchedule]: ...

    async def delete_round_schedule(self, session_id: uuid.UUID) -> None: ...

    async def get_ready_board(self, session_id: uuid.UUID) -> Optional[uuid.UUID]: ...

    async def wait_for_board_ready(self, session_id: uuid.UUID) -> None: ...

    async def add_ready_board(
        self, session_id: uuid.UUID, board_id: uuid.UUID
    ) -> None: ...

    async def is_board_ready(self, session_id: uuid.UUID) -> bool: ...

    async def peek_ready_board(self, session_id: uuid.UUID) -> Optional[uuid.UUID]: ...

    async def add_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None: ...

    async def remove_generation(
        self, session_id: uuid.UUID, generation_id: uuid.UUID
    ) -> None: ...

    async def is_generating(self, session_id: uuid.UUID) -> bool: ...

    async def set_lock_job_id(
        self, session_id: uuid.UUID, job_id: JobID | None
    ) -> None: ...

    async def get_lock_job_id(self, session_id: uuid.UUID) -> Optional[JobID]: ...

    async def is_waiting_for_round(self, session_id: uuid.UUID) -> bool: ...


__all__ = ["SessionRuntimeStore"]
