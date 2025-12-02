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


multi_websockets = WebsocketsRegistry()
