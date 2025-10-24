import uuid
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from algorithms.boards.grid import Grid
from backend import repositories, services
from backend.core.game.game import SingleplayerGameplay
from backend.models import game_models
from backend.repositories.exceptions import BoardNotFoundException
from backend.schemas.game_schemas import *
from backend.services.auth_service import CurrentUser, OptionalCurrentUser
from backend.services.exceptions import BoardNotExists

GameRepository = Annotated[repositories.GameRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
BoardService = Annotated[services.BoardService, Depends()]


class GameService:
    gameplays: dict[uuid.UUID, SingleplayerGameplay] = {}

    def __init__(
        self,
        board_service: BoardService,
        board_repo: BoardRepository,
        game_repo: GameRepository,
    ):
        self.board_service = board_service
        self.game_repo = game_repo
        self.board_repo = board_repo

    async def create_singleplayer_session(
        self, user: OptionalCurrentUser, new_game_input: NewGameInput
    ) -> NewGameResponse:
        try:
            if new_game_input.board_id:
                board = await self.board_repo.get_board_by_id(new_game_input.board_id)
            elif new_game_input.generation_settings and new_game_input.difficulty_level:
                board = await self.board_service.generate_board(
                    new_game_input.generation_settings,
                    new_game_input.difficulty_level,
                )
            elif new_game_input.difficulty_level:
                raise NotImplementedError(
                    "Random board generation based on difficulty level is not implemented yet"
                )
            else:
                raise ValueError("Invalid NewGameInput provided")

            db_gameplay = game_models.SingleplayerGameplay(
                user_id=user.id if user else None,
                board_id=board.id,
            )
            db_gameplay = await self.game_repo.add_gameplay(db_gameplay)

            grid = Grid(
                rows=board.board_type.rows,
                columns=board.board_type.columns,
                mined_fields=board.minefields,
            )

            gameplay = SingleplayerGameplay(gameplay_id=db_gameplay.id, grid=grid)
            self.gameplays[db_gameplay.id] = gameplay

            return NewGameResponse(
                gameplay_id=db_gameplay.id,
                board_id=board.id,
                start_field=board.start_field,
            )

        except BoardNotFoundException:
            raise BoardNotExists(
                f"Board with id {new_game_input.board_id} does not exist"
            ) from None

    async def get_gameplays(self, user: CurrentUser, pagination_params: Params):
        return await self.game_repo.get_gameplays(user.id, pagination_params)

    async def start_singleplayer_game(self, gameplay_id: uuid.UUID):
        gameplay = self.gameplays.get(gameplay_id)
        if not gameplay:
            raise ValueError("Gameplay not found")

    def _get_session(self, gameplay_id: uuid.UUID) -> SingleplayerGameplay:
        gameplay = self.gameplays.get(gameplay_id)
        if not gameplay:
            raise ValueError("Gameplay not found")
        return gameplay

    async def handle_game_action(
        self, gameplay_id: uuid.UUID, action: GameAction
    ) -> dict:
        game_actions = {
            "reveal_one": self._handle_reveal_one,
            "reveal_many": self._handle_reveal_many,
            "flag": self._handle_flag,
            "remove_flag": self._handle_remove_flag,
        }
        return await game_actions[action.type](gameplay_id, action)

    async def _handle_reveal_one(self, gameplay_id: uuid.UUID, action: RevealOne):
        session = self._get_session(gameplay_id)
        return session.reveal_one(action.x, action.y)

    async def _handle_reveal_many(self, gameplay_id: uuid.UUID, action: RevealMany):
        session = self._get_session(gameplay_id)
        return session.reveal_many(action.x, action.y)

    async def _handle_flag(self, gameplay_id: uuid.UUID, action: Flag):
        session = self._get_session(gameplay_id)
        return session.flag(action.x, action.y)

    async def _handle_remove_flag(self, gameplay_id: uuid.UUID, action: RemoveFlag):
        session = self._get_session(gameplay_id)
        return session.remove_flag(action.x, action.y)
