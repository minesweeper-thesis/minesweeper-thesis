import functools
from typing import Sequence

from backend.core.user import User
from backend.repositories.orm.user_orm import UserORM


async def _transformer(self, items: Sequence[UserORM]) -> list[User]:
    result = []
    for user in items:
        is_online = await self.is_user_online(user.id)
        result.append(user.to_user(is_online))
    return result


get_users_transformer = lambda self: functools.partial(_transformer, self)
