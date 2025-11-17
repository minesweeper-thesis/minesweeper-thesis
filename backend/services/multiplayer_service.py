import asyncio
import uuid
from typing import Annotated, Any, Awaitable, Callable, Optional

from fastapi import Depends

from backend import repositories
from backend.core.game import *
from backend.core.multiplayer import (
    IsSessionOver,
    MultiplayerGameplay,
    MultiplayerSession,
    MultiplayerSessionMessage,
)
from backend.lib.auth import CurrentUser
from backend.repositories.exceptions import *
from backend.services.exceptions import *

MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]


class MultiplayerService:
    def __init__(
        self,
        board_repo: BoardRepository,
        multiplayer_repo: MultiplayerRepository,
        user: CurrentUser,
    ):
        self.multiplayer_repo = multiplayer_repo
        self.board_repo = board_repo

        self.session: Optional[MultiplayerSession] = None
        self.user_id = user.id
        self.current_gameplay: Optional[MultiplayerGameplay] = None

        self._round_task: Optional[asyncio.Task] = None
        self._round_start_time: Optional[float] = None

    async def load_session(
        self,
        session_id: uuid.UUID,
        user: CurrentUser,
        send_data: Callable[[Any], Awaitable[None]],
    ):
        self.session = await self.multiplayer_repo.get_session(session_id)
        self.user_id = user.id

        self.session.send_data = send_data

        if user.id not in self.session.player_ids:
            raise ValueError("User is not part of this session")

    async def handle_multiplayer_session_message(
        self, message: MultiplayerSessionMessage
    ):
        if not self.session:
            raise RuntimeError("No session loaded")

        message.handle(self.session, self.user_id)

    async def handle_game_action(
        self, action: GameAction
    ) -> tuple[ActionResult, IsSessionOver]:
        if not self.session:
            raise RuntimeError("No session loaded")

        return (
            self.session.handle_game_action(action, self.user_id),
            self.session.is_session_over(),
        )
