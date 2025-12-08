import uuid
from typing import Any

from backend.lib.notification_system import create_game_notification
from backend.lib.websockets.websockets_registry import session_websockets
from backend.protocols.game_transport_protocol import GameTransport


class SessionGameTransport(GameTransport):
    def __init__(self, session_id: uuid.UUID):
        self.session_id = session_id

    async def send(self, receiver_id: uuid.UUID, event: Any) -> None:
        if session_websockets.is_connected(self.session_id, receiver_id):
            websocket = session_websockets.get(self.session_id, receiver_id)
            await websocket.send_text(create_game_notification(event))

    async def close(self, receiver_id: uuid.UUID) -> None:
        if session_websockets.is_connected(self.session_id, receiver_id):
            websocket = session_websockets.get(self.session_id, receiver_id)
            await websocket.close()


class GameTransportFactory:
    def create(self, session_id: uuid.UUID) -> GameTransport:
        return SessionGameTransport(session_id)


_game_transport_factory = GameTransportFactory()


def get_game_transport_factory() -> GameTransportFactory:
    return _game_transport_factory
