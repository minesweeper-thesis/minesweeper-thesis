import uuid
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class PendingGameplay:
    id: uuid.UUID
    status: Literal["generating", "ready"] = "generating"


class PendingGameplaysStore:
    def __init__(self):
        self._pending: dict[uuid.UUID, PendingGameplay] = {}

    def add(self, gameplay_id: uuid.UUID) -> None:
        self._pending[gameplay_id] = PendingGameplay(id=gameplay_id)

    def get(self, gameplay_id: uuid.UUID) -> Optional[PendingGameplay]:
        return self._pending.get(gameplay_id)

    def remove(self, gameplay_id: uuid.UUID) -> None:
        self._pending.pop(gameplay_id, None)

    def is_pending(self, gameplay_id: uuid.UUID) -> bool:
        return gameplay_id in self._pending

    def mark_ready(self, gameplay_id: uuid.UUID) -> None:
        pending = self._pending.get(gameplay_id)
        if pending:
            pending.status = "ready"


pending_store = PendingGameplaysStore()
