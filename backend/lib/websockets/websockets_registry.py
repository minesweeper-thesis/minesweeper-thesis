import uuid

from fastapi import WebSocket


class WebsocketsRegistry:
    def __init__(self) -> None:
        self._websockets: dict[uuid.UUID, WebSocket] = {}

    def get(self, id: uuid.UUID) -> WebSocket:
        return self._websockets[id]

    def add(self, id: uuid.UUID, websocket: WebSocket):
        self._websockets[id] = websocket

    def remove(self, id: uuid.UUID):
        self._websockets.pop(id, None)

    def is_connected(self, id: uuid.UUID) -> bool:
        return id in self._websockets


class SessionWebsocketsRegistry:
    def __init__(self) -> None:
        self._websockets: dict[uuid.UUID, dict[uuid.UUID, WebSocket]] = {}

    def get(self, session_id: uuid.UUID, user_id: uuid.UUID) -> WebSocket:
        return self._websockets[session_id][user_id]

    def add(self, session_id: uuid.UUID, user_id: uuid.UUID, websocket: WebSocket):
        if session_id not in self._websockets:
            self._websockets[session_id] = {}
        self._websockets[session_id][user_id] = websocket

    def remove(self, session_id: uuid.UUID, user_id: uuid.UUID):
        if session_id in self._websockets:
            self._websockets[session_id].pop(user_id, None)
            if not self._websockets[session_id]:
                self._websockets.pop(session_id)

    def is_connected(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return (
            session_id in self._websockets and user_id in self._websockets[session_id]
        )


session_websockets = SessionWebsocketsRegistry()
