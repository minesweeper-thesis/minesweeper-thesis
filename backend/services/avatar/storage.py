from typing import Protocol


class AvatarStorage(Protocol):
    async def save(self, filename: str, content: bytes) -> str: ...

    async def delete(self, filename: str) -> None: ...
