import uuid
from typing import Any

from backend.lib.notification_system import create_game_notification
from backend.lib.websockets.websockets_registry import multi_websockets
from backend.protocols.game_transport import GameTransport

# user_events: dict[uuid.UUID, list[Any]] = defaultdict(list)


class WebSocketGameTransport(GameTransport):
    async def send(self, receiver_id: uuid.UUID, event: Any) -> None:
        if receiver_id in multi_websockets._websockets:
            websocket = multi_websockets.get(receiver_id)
            await websocket.send_text(create_game_notification(event))
        # else:
        #     user_events[receiver_id].append(event)

    async def broadcast(self, event: Any) -> None:
        for receiver_id in multi_websockets._websockets:
            websocket = multi_websockets.get(receiver_id)
            await websocket.send_text(create_game_notification(event))

    async def close_all(self) -> None:
        for receiver_id in multi_websockets._websockets:
            websocket = multi_websockets.get(receiver_id)
            await websocket.close()


__all__ = ["WebSocketGameTransport"]
