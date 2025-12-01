from typing import Optional

from backend.core.board import DifficultyLevel, GenerationSettings


class UsersNotFriends(Exception):
    pass


class FriendRequestNotExists(Exception):
    pass


class FriendRequestAlreadySent(Exception):
    pass


class UsersAlreadyFriends(Exception):
    pass


class CannotFriendRequestYourself(Exception):
    pass


class BoardNotExists(Exception):
    pass


class RequestedFriendNotExists(Exception):
    pass


class SolvedAllBoards(Exception):
    def __init__(
        self,
        difficulty_level: DifficultyLevel,
        generation_settings: Optional[GenerationSettings] = None,
    ):
        self.difficulty_level = difficulty_level
        self.generation_settings = generation_settings


class GameplayAlreadyFinished(Exception):
    pass


class GameplayNotExists(Exception):
    pass


__all__ = [
    "UsersNotFriends",
    "FriendRequestNotExists",
    "FriendRequestAlreadySent",
    "UsersAlreadyFriends",
    "CannotFriendRequestYourself",
    "BoardNotExists",
    "RequestedFriendNotExists",
    "SolvedAllBoards",
    "GameplayAlreadyFinished",
    "GameplayNotExists",
]
