import uuid
from typing import Any, Protocol


class LobbyTransport(Protocol):
    async def broadcast(self, event: Any) -> None: ...
    async def send(self, receiver_id: uuid.UUID, data: Any) -> None: ...
    async def close(self, receiver_id: uuid.UUID) -> None: ...


class LobbyTransportFactory(Protocol):
    def create(self, lobby_id: uuid.UUID) -> LobbyTransport: ...


__all__ = ["LobbyTransport", "LobbyTransportFactory"]
