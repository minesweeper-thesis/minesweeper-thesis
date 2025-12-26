import logging
import uuid

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class LobbyWebsocketsRegistry:
    def __init__(self) -> None:
        self._websockets: dict[uuid.UUID, dict[uuid.UUID, WebSocket]] = {}

    def get(self, lobby_id: uuid.UUID, user_id: uuid.UUID) -> WebSocket:
        logger.debug(f"get(lobby_id={lobby_id}, user_id={user_id})")
        return self._websockets[lobby_id][user_id]

    def add(self, lobby_id: uuid.UUID, user_id: uuid.UUID, websocket: WebSocket):
        logger.debug(f"add(lobby_id={lobby_id}, user_id={user_id})")
        if lobby_id not in self._websockets:
            self._websockets[lobby_id] = {}
        self._websockets[lobby_id][user_id] = websocket
        logger.debug(f"Lobby WebSocket added for user {user_id} in lobby {lobby_id}")

    def remove(self, lobby_id: uuid.UUID, user_id: uuid.UUID):
        logger.debug(f"remove(lobby_id={lobby_id}, user_id={user_id})")
        if lobby_id in self._websockets:
            self._websockets[lobby_id].pop(user_id, None)
            logger.debug(
                f"Lobby WebSocket removed for user {user_id} in lobby {lobby_id}"
            )
            if not self._websockets[lobby_id]:
                self._websockets.pop(lobby_id)
                logger.debug(f"Lobby {lobby_id} removed (no more users)")

    def is_connected(self, lobby_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return lobby_id in self._websockets and user_id in self._websockets[lobby_id]


lobby_websockets = LobbyWebsocketsRegistry()
