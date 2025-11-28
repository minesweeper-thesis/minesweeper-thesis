import os
import uuid
from typing import Protocol

from .local import LocalAvatarStorage
from .remote import RemoteAvatarStorage

AWS_ACCESS_KEY_ID = os.getenv("BUCKETEER_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("BUCKETEER_AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("BUCKETEER_AWS_REGION")
AWS_BUCKET_NAME = os.getenv("BUCKETEER_BUCKET_NAME")


class AvatarStorage(Protocol):
    async def save(self, user_id: uuid.UUID, content: bytes) -> str: ...

    async def delete(self, avatar_url: str) -> None: ...


def get_avatar_storage() -> AvatarStorage:
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_REGION and AWS_BUCKET_NAME:
        return RemoteAvatarStorage(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_region=AWS_REGION,
            aws_bucket_name=AWS_BUCKET_NAME,
        )
    else:
        return LocalAvatarStorage()
