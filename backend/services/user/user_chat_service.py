import uuid
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core.user import User, UserChatMessage
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.services.exceptions import *

UserRepository = Annotated[repositories.UserRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]


class UserChatService:
    def __init__(
        self,
        user_repo: UserRepository,
        notification_system: NotificationSystem,
    ):
        self.user_repo = user_repo
        self.notification_system = notification_system

    async def send_chat_message(
        self,
        user: User,
        to_id: uuid.UUID,
        content: str,
    ):
        to_user = await self.user_repo.get_user(to_id)

        message = UserChatMessage(
            from_user=user,
            to=to_user,
            content=content,
            timestamp=datetime.now(),
        )

        await self.user_repo.add_message(message)

        await self.notification_system.notify(to_user.id, message)

    async def get_chat_messages(
        self,
        user: User,
        to_id: uuid.UUID,
        pagination_params: Params,
    ):
        to_user = await self.user_repo.get_user(to_id)
        if not to_user:
            raise ValueError("User not found")

        return await self.user_repo.get_messages(user.id, to_id, pagination_params)
