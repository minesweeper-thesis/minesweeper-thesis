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


class SpecificBoardAnonymousUser(Exception):
    pass


class BoardAlreadyPlayed(Exception):
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


class UserNotExists(Exception):
    pass


class UserNotHost(Exception):
    pass


class LobbyNotExists(Exception):
    pass


class SessionNotExists(Exception):
    pass


class InvitationNotExists(Exception):
    pass


class GenerationError(Exception):
    pass


class SessionActive(Exception):
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
    "UserNotExists",
    "UserNotHost",
    "LobbyNotExists",
    "InvitationNotExists",
    "GenerationError",
    "SessionActive",
    "BoardAlreadyPlayed",
    "SpecificBoardAnonymousUser",
]
