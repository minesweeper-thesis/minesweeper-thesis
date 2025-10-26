from fastapi import FastAPI

from .auth_router import auth_router
from .game_router import game_exceptions, game_router
from .stats_router import stats_router
from .user_router import user_exceptions, user_router

_exceptions = {
    **user_exceptions,
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
    "stats_router",
    "game_router",
    "user_exceptions",
    "register_exceptions",
]
