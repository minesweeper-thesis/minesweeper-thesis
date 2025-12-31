import logging
import uuid
from typing import Any

from backend.lib.notification_system import create_game_notification
from backend.lib.websockets.lobby_websockets import lobby_websockets
from backend.protocols.lobby_transport_protocol import LobbyTransport

logger = logging.getLogger(__name__)


class LobbyWebsocketsTransport(LobbyTransport):
    def __init__(self, lobby_id: uuid.UUID):
        self.lobby_id = lobby_id

    async def broadcast(self, event: Any) -> None:
        logger.debug(f"broadcast(event={event}, lobby_id={self.lobby_id})")
        connected_users = lobby_websockets.get_connected_users(self.lobby_id)
        for user_id in connected_users:
            await self.send(user_id, event)

    async def send(self, receiver_id: uuid.UUID, event: Any) -> None:
        logger.debug(
            f"send(receiver_id={receiver_id}, event={event}, lobby_id={self.lobby_id})"
        )
        if lobby_websockets.is_connected(self.lobby_id, receiver_id):
            websocket = lobby_websockets.get(self.lobby_id, receiver_id)
            logger.debug(
                f"Sending game event to {receiver_id} in lobby {self.lobby_id}: {event}"
            )
            await websocket.send_text(create_game_notification(event))
        else:
            logger.warning(
                f"Cannot send game event to {receiver_id} in lobby {self.lobby_id}: not connected"
            )

    async def close(self, receiver_id: uuid.UUID) -> None:
        logger.debug(f"close(receiver_id={receiver_id}, lobby_id={self.lobby_id})")
        if lobby_websockets.is_connected(self.lobby_id, receiver_id):
            websocket = lobby_websockets.get(self.lobby_id, receiver_id)
            logger.info(f"Closing websocket for {receiver_id} in lobby {self.lobby_id}")
            await websocket.close()


class LobbyTransportFactory:
    def get(self, lobby_id: uuid.UUID) -> LobbyTransport:
        logger.debug(f"LobbyTransportFactory.get(lobby_id={lobby_id})")
        return LobbyWebsocketsTransport(lobby_id)


_lobby_transport_factory = LobbyTransportFactory()


def get_lobby_transport_factory() -> LobbyTransportFactory:
    return _lobby_transport_factory
