from .local import LocalAvatarStorage
from .storage import AvatarStorage


def get_avatar_storage() -> AvatarStorage:
    return LocalAvatarStorage()
