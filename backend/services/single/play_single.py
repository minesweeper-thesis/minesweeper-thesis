import uuid
from contextlib import suppress
from typing import Annotated, Optional

from fastapi import Depends
from fastapi_pagination import Params

from backend import protocols, repositories
from backend.core.game import *
from backend.core.game.game_actions import GameAction, GameActionResult
from backend.core.single import SingleplayerGameplay
from backend.lib.auth import CurrentUser
from backend.lib.pending_boards import get_pending_boards_store
from backend.repositories.exceptions import *
from backend.services.dto import *
from backend.services.exceptions import *
from backend.services.single.single_exceptions import GenerationTimeout

SingleplayerRepository = Annotated[repositories.SingleplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
PendingGameplaysStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]


class PlaySingleUseCase:
    def __init__(
        self,
        board_repo: BoardRepository,
        game_repo: SingleplayerRepository,
        pending_store: PendingGameplaysStore,
    ):
        self.game_repo = game_repo
        self.board_repo = board_repo
        self.pending_store = pending_store
        self.gameplay: Optional[SingleplayerGameplay] = None

    async def load_gameplay(
        self,
        gameplay_id: uuid.UUID,
        timeout: float = 120.0,
    ):
        pending = await self.pending_store.get_pending_gameplay(gameplay_id)

        if pending is not None:
            pending = await self.pending_store.wait_for_ready(
                gameplay_id, timeout=timeout
            )
            if pending is None or pending.board_id is None:
                raise GenerationTimeout()

            board = await self.board_repo.get_board_by_id(pending.board_id)

            gameplay = SingleplayerGameplay(
                id=gameplay_id,
                board=board,
                mode=pending.metadata.mode,
            )
            await self.game_repo.add_gameplay(
                gameplay, board.id, pending.metadata.user_id
            )

        try:
            await self._set_gameplay(gameplay_id)
            assert self.gameplay is not None

            if self.gameplay.status == "finished":
                raise GameplayAlreadyFinished()

            return self.get_game_state()

        except GameplayNotFound:
            raise GameplayNotExists(
                f"Gameplay with id {gameplay_id} does not exist"
            ) from None

    async def _set_gameplay(self, gameplay_id: uuid.UUID):
        gameplay = await self.game_repo.get_gameplay_by_id(gameplay_id)
        self.gameplay = gameplay

    async def get_gameplays(self, user: CurrentUser, pagination_params: Params):
        return await self.game_repo.get_gameplays(user.id, pagination_params)

    async def execute_action(self, action: GameAction) -> Optional[GameActionResult]:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        with suppress(InvalidAction):
            return action.execute(self.gameplay)

        return None

    def get_game_state(self) -> GameState:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        return self.gameplay.get_game_state()

    async def is_game_over(self) -> bool:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        return self.gameplay.is_game_over()

    async def get_game_over_result(self) -> GameOverResult:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        game_state = self.gameplay.get_game_state()

        assert game_state.result is not None

        return GameOverResult(
            result=game_state.result,
            full_board=self.gameplay.grid.grid,
            elapsed_time=self.gameplay.elapsed_time,
            loss_cause=self.gameplay.loss_cause,
        )

    async def save_gameplay_progress(self):
        if self.gameplay is None:
            return

        if self.gameplay.status == "in_progress":
            self.gameplay.update_elapsed_time()

        await self.game_repo.update_gameplay(self.gameplay)


__all__ = ["PlaySingleUseCase", "GenerationTimeout"]
