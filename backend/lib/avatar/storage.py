import uuid
from typing import Protocol


class AvatarStorage(Protocol):
    async def save(self, user_id: uuid.UUID, content: bytes) -> str: ...

    async def delete(self, avatar_url: str) -> None: ...
