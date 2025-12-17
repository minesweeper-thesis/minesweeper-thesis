import logging
import uuid
from datetime import datetime

from fastapi_pagination import Params

from backend.protocols.user_repo_protocol import UserNotFound
from backend.services.exceptions import UserNotExists

logger = logging.getLogger(__name__)

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
        logger.debug(
            f"send_chat_message(from_user={user.id}, to_id={to_id}, content_len={len(content)})"
        )
        to_user = await self.user_repo.get_user(to_id)

        message = UserChatMessage(
            from_user=user,
            to=to_user,
            content=content,
            timestamp=datetime.now(),
        )

        await self.user_repo.add_message(message)

        await self.notification_system.notify(to_user.id, message)
        logger.info(f"Chat message sent from {user.id} to {to_id}")

    async def get_chat_messages(
        self,
        user: User,
        to_id: uuid.UUID,
        pagination_params: Params,
    ):
        logger.debug(f"get_chat_messages(user_id={user.id}, to_id={to_id})")
        try:
            await self.user_repo.get_user(to_id)
        except UserNotFound:
            logger.warning(f"User with id {to_id} does not exist")
            raise UserNotExists() from None

        return await self.user_repo.get_messages(user.id, to_id, pagination_params)
