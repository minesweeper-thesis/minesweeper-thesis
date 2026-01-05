class NotAuthorizedToJoinLobby(Exception):
    pass


class SessionActive(Exception):
    pass


__all__ = ["NotAuthorizedToJoinLobby", "SessionActive"]
