import uuid
from typing import Any, Protocol


class LobbyTransport(Protocol):
    async def broadcast(self, event: Any) -> None: ...
    async def send(self, receiver_id: uuid.UUID, data: Any) -> None: ...
    async def send_many(
        self, events_by_receiver: dict[uuid.UUID, list[Any]]
    ) -> None: ...


class LobbyTransportFactory(Protocol):
    def get(self, lobby_id: uuid.UUID) -> LobbyTransport: ...


__all__ = ["LobbyTransport", "LobbyTransportFactory"]
