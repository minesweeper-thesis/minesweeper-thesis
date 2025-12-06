from dataclasses import dataclass
from datetime import datetime

from backend.core.user.user import User


@dataclass
class UserChatMessage:
    from_user: User
    to: User
    content: str
    timestamp: datetime


__all__ = ["UserChatMessage"]
