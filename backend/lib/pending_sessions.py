import uuid
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class PendingSession:
    id: uuid.UUID
    status: Literal["generating", "ready"] = "generating"


class PendingSessionsStore:
    def __init__(self) -> None:
        self._pending: dict[uuid.UUID, PendingSession] = {}

    def add(self, session_id: uuid.UUID) -> None:
        self._pending[session_id] = PendingSession(id=session_id)

    def get(self, session_id: uuid.UUID) -> Optional[PendingSession]:
        return self._pending.get(session_id)

    def remove(self, session_id: uuid.UUID) -> None:
        self._pending.pop(session_id, None)

    def is_pending(self, session_id: uuid.UUID) -> bool:
        return session_id in self._pending

    def mark_ready(self, session_id: uuid.UUID) -> None:
        pending = self._pending.get(session_id)
        if pending:
            pending.status = "ready"


pending_sessions_store = PendingSessionsStore()
