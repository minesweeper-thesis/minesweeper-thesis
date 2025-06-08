from fastapi import APIRouter, Depends, Response

from backend.services import auth_service, user_service

from ..db import *
from ..models import *
from ..schemas import *

user_router = APIRouter()


@user_router.post("/gameplays", status_code=204)
async def save_gameplay(
    gameplay: GameplaySchema, user: User = Depends(auth_service.get_current_user)
):
    """Saves gameplay for current user"""
    await user_service.save_gameplay(
        user.id, gameplay.board_id, gameplay.score, gameplay.time, gameplay.used_prompts
    )


@user_router.get("/gameplays", response_model=list[GameplaySchema])
async def get_gameplays(user: User = Depends(auth_service.get_current_user)):
    """Gets all gameplays for current user"""
    return await user_service.get_gameplays(user.id)
