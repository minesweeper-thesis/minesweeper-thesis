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


class SessionWebsocketsRegistry:
    def __init__(self) -> None:
        self._websockets: dict[uuid.UUID, dict[uuid.UUID, WebSocket]] = {}

    def get(self, session_id: uuid.UUID, user_id: uuid.UUID) -> WebSocket:
        logger.debug(f"get(session_id={session_id}, user_id={user_id})")
        return self._websockets[session_id][user_id]

    def add(self, session_id: uuid.UUID, user_id: uuid.UUID, websocket: WebSocket):
        logger.debug(f"add(session_id={session_id}, user_id={user_id})")
        if session_id not in self._websockets:
            self._websockets[session_id] = {}
        self._websockets[session_id][user_id] = websocket
        logger.debug(
            f"Session WebSocket added for user {user_id} in session {session_id}"
        )

    def remove(self, session_id: uuid.UUID, user_id: uuid.UUID):
        logger.debug(f"remove(session_id={session_id}, user_id={user_id})")
        if session_id in self._websockets:
            self._websockets[session_id].pop(user_id, None)
            logger.debug(
                f"Session WebSocket removed for user {user_id} in session {session_id}"
            )
            if not self._websockets[session_id]:
                self._websockets.pop(session_id)
                logger.debug(f"Session {session_id} removed (no more users)")

    def is_connected(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return (
            session_id in self._websockets and user_id in self._websockets[session_id]
        )


session_websockets = SessionWebsocketsRegistry()
