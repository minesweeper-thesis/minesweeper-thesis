import os
import uuid

import filetype

from backend.config import BACKEND_URL

from . import AvatarStorage

STATIC_AVATAR_DIR = "img"


def add_file_extension(filename: str, content: bytes) -> str:
    kind = filetype.guess(content)

    if kind is None:
        raise ValueError("Invalid file content type")

    ext = kind.extension
    if not filename.lower().endswith(f".{ext}"):
        filename = f"{filename}.{ext}"

    return filename


class LocalAvatarStorage(AvatarStorage):
    def __init__(self, static_dir: str = STATIC_AVATAR_DIR):
        self.static_dir = static_dir
        os.makedirs(self.static_dir, exist_ok=True)

    async def save(self, user_id: uuid.UUID, content: bytes) -> str:
        filename = add_file_extension(str(user_id), content)
        file_path = os.path.join(self.static_dir, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        return self._get_url(filename)

    def _get_url(self, filename: str) -> str:
        url = f"{BACKEND_URL}/{self.static_dir}/{filename}"
        return url

    async def delete(self, avatar_url: str) -> None:
        filename = avatar_url.split("/")[-1]
        file_path = os.path.join(self.static_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
