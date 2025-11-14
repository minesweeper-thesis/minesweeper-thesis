from fastapi import FastAPI

from .auth_router import auth_router
from .friends_router import friend_requests_router, friends_exceptions, friends_router
from .game_router import game_exceptions, game_router
from .lobby_router import invitations_router, lobby_router
from .notifications_router import notifications_router
from .stats_router import stats_router
from .user_router import user_exceptions, user_router

_exceptions = {
    **user_exceptions,
    **friends_exceptions,
    **game_exceptions,
}


def register_exceptions(app: FastAPI):
    for service_exception, router_exception in _exceptions.items():

        async def handler(request, exception, router_exception=router_exception):
            raise router_exception

        app.add_exception_handler(service_exception, handler)


__all__ = [
    "auth_router",
    "user_router",
    "friends_router",
    "friend_requests_router",
    "lobby_router",
    "invitations_router",
    "stats_router",
    "game_router",
    "user_exceptions",
    "friends_exceptions",
    "register_exceptions",
    "notifications_router",
]
