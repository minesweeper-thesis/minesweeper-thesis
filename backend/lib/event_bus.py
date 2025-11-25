import asyncio
from abc import ABC, abstractmethod
from typing import Any


class EventBus(ABC):
    @abstractmethod
    async def publish(self, channel: str, message: dict[str, Any]) -> None: ...

    @abstractmethod
    async def subscribe(self, channel: str) -> asyncio.Queue[dict[str, Any]]: ...

    @abstractmethod
    async def unsubscribe(
        self, channel: str, queue: asyncio.Queue[dict[str, Any]]
    ) -> None: ...

    @abstractmethod
    async def wait_for_message(
        self, channel: str, timeout: float | None = None
    ) -> dict[str, Any] | None: ...


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        queues = self._subscribers.get(channel, [])
        for queue in queues:
            await queue.put(message)

    async def subscribe(self, channel: str) -> asyncio.Queue[dict[str, Any]]:
        if channel not in self._subscribers:
            self._subscribers[channel] = []

        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[channel].append(queue)
        return queue

    async def unsubscribe(
        self, channel: str, queue: asyncio.Queue[dict[str, Any]]
    ) -> None:
        if channel in self._subscribers:
            try:
                self._subscribers[channel].remove(queue)
            except ValueError:
                pass

            if not self._subscribers[channel]:
                del self._subscribers[channel]

    async def wait_for_message(
        self, channel: str, timeout: float | None = None
    ) -> dict[str, Any] | None:
        queue = await self.subscribe(channel)
        try:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            return message
        except asyncio.TimeoutError:
            return None
        finally:
            await self.unsubscribe(channel, queue)


event_bus: EventBus = InMemoryEventBus()
