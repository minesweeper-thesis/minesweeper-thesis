import uuid

from backend.routers.schemas.lobby.lobby_schemas import create_notification
from backend.routers.websockets.connections_manager import connections_manager


class NotificationSystem:
    async def notify(self, receiver_id: uuid.UUID, data):
        if connections_manager.is_user_online(receiver_id):
            websocket = connections_manager.get(receiver_id)
            await websocket.send_text(create_notification(data))


def get_notification_system() -> NotificationSystem:
    return NotificationSystem()
