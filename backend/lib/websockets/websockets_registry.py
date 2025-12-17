import logging
import uuid

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebsocketsRegistry:
    def __init__(self) -> None:
        self._websockets: dict[uuid.UUID, WebSocket] = {}

    def get(self, id: uuid.UUID) -> WebSocket:
        logger.debug(f"get(id={id})")
        return self._websockets[id]

    def add(self, id: uuid.UUID, websocket: WebSocket):
        logger.debug(f"add(id={id})")
        self._websockets[id] = websocket
        logger.debug(f"WebSocket added for {id}")

    def remove(self, id: uuid.UUID):
        logger.debug(f"remove(id={id})")
        self._websockets.pop(id, None)
        logger.debug(f"WebSocket removed for {id}")

    def is_connected(self, id: uuid.UUID) -> bool:
        logger.debug(f"is_connected(id={id})")
        return id in self._websockets
