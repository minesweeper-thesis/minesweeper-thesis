import uuid
from datetime import datetime
from typing import Optional, Protocol


class SessionRuntimeStore(Protocol):
    async def set_round_schedule(
        self,
        session_id: uuid.UUID,
        countdown_to: datetime,
        start_at: datetime,
        end_at: datetime,
    ) -> None: ...

    async def get_round_schedule(
        self, session_id: uuid.UUID
    ) -> tuple[Optional[datetime], Optional[datetime], Optional[datetime]]: ...

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
