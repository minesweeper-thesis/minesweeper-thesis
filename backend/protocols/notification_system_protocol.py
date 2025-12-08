import uuid
from typing import Protocol


class NotificationSystem(Protocol):
    async def notify(self, receiver_id: uuid.UUID, data): ...


__all__ = ["NotificationSystem"]
