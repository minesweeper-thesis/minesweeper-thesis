import uuid
from datetime import datetime
from typing import Optional, Protocol


class SessionRuntimeStore(Protocol):
    async def set_countdown(
        self, session_id: uuid.UUID, countdown_to: datetime, start_at: datetime
    ) -> None: ...

    async def get_countdown(
        self, session_id: uuid.UUID
    ) -> tuple[Optional[datetime], Optional[datetime]]: ...

    async def clear_countdown(self, session_id: uuid.UUID) -> None: ...
