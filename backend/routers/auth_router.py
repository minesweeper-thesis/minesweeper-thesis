from fastapi import APIRouter

from backend.lib.auth import auth_backend, fastapi_users

from .schemas.user import *

auth_router = APIRouter(tags=["auth"])


auth_router.include_router(fastapi_users.get_auth_router(auth_backend))

auth_router.include_router(
    fastapi_users.get_register_router(CurrentUserResponse, UserCreateRequest)
)

auth_router.include_router(
    fastapi_users.get_users_router(CurrentUserResponse, UserUpdateRequest)
)
