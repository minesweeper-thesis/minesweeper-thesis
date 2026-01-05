import logging
import uuid

from . import OnlineUsersStore

logger = logging.getLogger(__name__)


class LocalOnlineUsersStore(OnlineUsersStore):
    def __init__(self) -> None:
        self.online_users: set[uuid.UUID] = set()

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        logger.debug(f"is_user_online(user_id={user_id})")
        return user_id in self.online_users

    async def set_user_online(self, user_id: uuid.UUID):
        logger.debug(f"set_user_online(user_id={user_id})")
        self.online_users.add(user_id)
        logger.info(f"User {user_id} set to ONLINE (total: {len(self.online_users)})")

    async def set_user_offline(self, user_id: uuid.UUID):
        logger.debug(f"set_user_offline(user_id={user_id})")
        self.online_users.discard(user_id)
        logger.info(f"User {user_id} set to OFFLINE (total: {len(self.online_users)})")
