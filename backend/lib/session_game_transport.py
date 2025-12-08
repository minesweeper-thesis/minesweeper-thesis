import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

from backend.lib.notification_system import create_game_notification
from backend.lib.websockets.websockets_registry import session_websockets
from backend.protocols.game_transport_protocol import GameTransport


class SessionGameTransport(GameTransport):
    def __init__(self, session_id: uuid.UUID):
        self.session_id = session_id

    async def send(self, receiver_id: uuid.UUID, event: Any) -> None:
        logger.debug(
            f"send(receiver_id={receiver_id}, event={type(event).__name__}, session_id={self.session_id})"
        )
        if session_websockets.is_connected(self.session_id, receiver_id):
            websocket = session_websockets.get(self.session_id, receiver_id)
            logger.debug(
                f"Sending game event to {receiver_id} in session {self.session_id}: {type(event).__name__}"
            )
            await websocket.send_text(create_game_notification(event))
        else:
            logger.warning(
                f"Cannot send game event to {receiver_id} in session {self.session_id}: not connected"
            )

    async def close(self, receiver_id: uuid.UUID) -> None:
        logger.debug(f"close(receiver_id={receiver_id}, session_id={self.session_id})")
        if session_websockets.is_connected(self.session_id, receiver_id):
            websocket = session_websockets.get(self.session_id, receiver_id)
            logger.info(
                f"Closing websocket for {receiver_id} in session {self.session_id}"
            )
            await websocket.close()


class GameTransportFactory:
    def create(self, session_id: uuid.UUID) -> GameTransport:
        logger.debug(f"GameTransportFactory.create(session_id={session_id})")
        return SessionGameTransport(session_id)


_game_transport_factory = GameTransportFactory()


def get_game_transport_factory() -> GameTransportFactory:
    return _game_transport_factory
