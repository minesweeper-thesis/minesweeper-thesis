import uuid
from datetime import datetime

from fastapi_pagination import Params

from backend.core.user import User, UserChatMessage
from backend.di.dependencies import *
from backend.services.exceptions import *


class UserChatService:
    def __init__(
        self,
        user_repo: UserRepositoryDep,
        notification_system: NotificationSystemDep,
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
