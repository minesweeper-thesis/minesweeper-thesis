import uuid

from fastapi import WebSocket

from backend.lib.websockets_registry import WebsocketsRegistry


class ConnectionsManager(WebsocketsRegistry):
    user_websockets: dict[uuid.UUID, WebSocket] = {}

    @classmethod
    def is_user_online(cls, user_id: uuid.UUID) -> bool:
        return user_id in cls.user_websockets
