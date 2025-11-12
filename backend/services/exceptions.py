from backend.core.board import DifficultyLevel


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
    def __init__(self, difficulty_level: DifficultyLevel):
        self.difficulty_level = difficulty_level


class GameplayAlreadyFinished(Exception):
    pass


class GameplayNotExists(Exception):
    pass
