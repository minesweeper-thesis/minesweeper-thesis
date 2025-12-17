import uuid
from typing import Protocol

from backend.config import (
    AWS_ACCESS_KEY_ID,
    AWS_BUCKET_NAME,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
)


class AvatarStorage(Protocol):
    async def save(self, user_id: uuid.UUID, content: bytes) -> str: ...

    async def delete(self, avatar_url: str) -> None: ...


def get_avatar_storage() -> AvatarStorage:
    from .local import LocalAvatarStorage
    from .remote import RemoteAvatarStorage

    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_REGION and AWS_BUCKET_NAME:
        return RemoteAvatarStorage(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY),
            aws_region=AWS_REGION,
            aws_bucket_name=AWS_BUCKET_NAME,
        )
    else:
        return LocalAvatarStorage()
