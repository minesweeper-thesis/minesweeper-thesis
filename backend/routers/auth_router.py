from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from backend.lib.auth import auth_backend, fastapi_users, get_current_user

from .schemas.user_schemas import *

auth_router = APIRouter(tags=["auth"])


auth_router.include_router(fastapi_users.get_auth_router(auth_backend))

auth_router.include_router(
    fastapi_users.get_register_router(CurrentUserResponse, UserCreateRequest)
)

auth_router.include_router(
    fastapi_users.get_users_router(CurrentUserResponse, UserUpdateRequest)
)


@auth_router.post(
    "/logout", response_class=RedirectResponse, dependencies=[Depends(get_current_user)]
)
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(key="auth")
    return response
