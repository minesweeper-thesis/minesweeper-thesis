import uuid

from fastapi import WebSocket


class WebsocketsRegistry:
    _websockets: dict[uuid.UUID, WebSocket] = {}

    @classmethod
    def get(cls, id: uuid.UUID) -> WebSocket:
        return cls._websockets[id]

    @classmethod
    def add(cls, id: uuid.UUID, websocket: WebSocket):
        cls._websockets[id] = websocket

    @classmethod
    def remove(cls, id: uuid.UUID):
        cls._websockets.pop(id, None)


multi_websockets = WebsocketsRegistry()
