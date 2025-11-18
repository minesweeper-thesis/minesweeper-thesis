import uuid


class LocalOnlineUsersStore:
    online_users = set()

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        return user_id in self.online_users

    async def set_user_online(self, user_id: uuid.UUID):
        self.online_users.add(user_id)

    async def set_user_offline(self, user_id: uuid.UUID):
        self.online_users.discard(user_id)
