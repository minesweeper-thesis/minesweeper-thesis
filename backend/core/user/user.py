import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class Avatar:
    url: str


class User:
    def __init__(
        self,
        id: uuid.UUID,
        nickname: str,
        email: str,
        settings: dict,
        is_online: bool,
        avatar: Optional[Avatar] = None,
    ):
        self.id = id
        self.nickname = nickname
        self.email = email
        self.settings = settings
        self.avatar = avatar
        self.is_online = is_online

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, User):
            return False
        return self.id == value.id
