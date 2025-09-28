from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from ..db import *
from ..models import *
from ..schemas import *
from ..services.auth_service import auth_backend, fastapi_users, get_current_user

auth_router = APIRouter()


auth_router.include_router(fastapi_users.get_auth_router(auth_backend))

auth_router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))

auth_router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate))


@auth_router.post(
    "/logout", response_class=RedirectResponse, dependencies=[Depends(get_current_user)]
)
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(key="auth")
    return response
