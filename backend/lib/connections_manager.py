import uuid

from fastapi import WebSocket


class ConnectionsManager:
    user_websockets: dict[uuid.UUID, WebSocket] = {}

    @classmethod
    def get_user_websocket(cls, user_id: uuid.UUID) -> WebSocket:
        return cls.user_websockets.get(user_id)  # type: ignore

    @classmethod
    def add_user(cls, user_id: uuid.UUID, websocket: WebSocket):
        cls.user_websockets[user_id] = websocket

    @classmethod
    def remove_user(cls, user_id: uuid.UUID):
        cls.user_websockets.pop(user_id, None)

    @classmethod
    def is_user_online(cls, user_id: uuid.UUID) -> bool:
        return user_id in cls.user_websockets
