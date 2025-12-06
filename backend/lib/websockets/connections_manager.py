import uuid

from backend.lib.websockets.websockets_registry import WebsocketsRegistry


class ConnectionsManager(WebsocketsRegistry):
    def __init__(self) -> None:
        super().__init__()

    def is_user_online(self, user_id: uuid.UUID) -> bool:
        return user_id in self._websockets


connections_manager = ConnectionsManager()
