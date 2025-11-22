from typing import Awaitable, Callable, Protocol

type EventCallback = Callable[[], Awaitable[None]]


class EventBus(Protocol):
    async def publish(self, channel: str, message: dict) -> None: ...

    async def subscribe(self, channel: str, callback: EventCallback) -> None: ...

    async def unsubscribe(self, channel: str) -> None: ...


class InMemoryEventBus(EventBus):
    def __init__(self):
        self._subscribers: dict[str, list[EventCallback]] = {}

    async def publish(self, channel: str, message: dict) -> None:
        callbacks = self._subscribers.get(channel, [])
        for callback in callbacks:
            await callback()

    async def subscribe(self, channel: str, callback: EventCallback) -> None:
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)

    async def unsubscribe(self, channel: str) -> None:
        self._subscribers.pop(channel, None)


event_bus = InMemoryEventBus()
