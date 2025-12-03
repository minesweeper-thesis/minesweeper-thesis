import uuid
from typing import Any, Protocol


class GameTransport(Protocol):
    async def send(self, receiver_id: uuid.UUID, data: Any) -> None: ...
    async def broadcast(self, data: Any) -> None: ...
    async def close_all(self) -> None: ...


__all_ = ["GameTransport"]
