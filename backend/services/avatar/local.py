import os
import urllib.parse

from .storage import AvatarStorage

STATIC_AVATAR_DIR = "img"


class LocalAvatarStorage(AvatarStorage):
    def __init__(self, static_dir: str = STATIC_AVATAR_DIR):
        self.static_dir = static_dir
        os.makedirs(self.static_dir, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        file_path = os.path.join(self.static_dir, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        return self._get_url(filename)

    def _get_url(self, filename: str) -> str:
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        url = f"{base_url}/{self.static_dir}/{urllib.parse.quote(filename)}"
        return url

    async def delete(self, filename: str) -> None:
        file_path = os.path.join(self.static_dir, filename)
        print(file_path)
        os.remove(file_path)
