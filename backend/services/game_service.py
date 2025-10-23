from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from backend import repositories, services
from backend.models import game
from backend.repositories.exceptions import BoardNotFoundException
from backend.schemas.game import NewGameInput, NewGameOutput
from backend.services.auth_service import CurrentUser, OptionalCurrentUser
from backend.services.exceptions import BoardNotExists

GameRepository = Annotated[repositories.GameRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
BoardService = Annotated[services.BoardService, Depends()]


class GameService:
    def __init__(
        self,
        board_service: BoardService,
        board_repo: BoardRepository,
        game_repo: GameRepository,
    ):
        self.board_service = board_service
        self.game_repo = game_repo
        self.board_repo = board_repo

    async def start_singleplayer_game(
        self, user: OptionalCurrentUser, new_game_input: NewGameInput
    ) -> NewGameOutput:
        try:
            if new_game_input.board_id:
                board = await self.board_repo.get_board_by_id(new_game_input.board_id)
            elif new_game_input.generation_settings:
                board = await self.board_service.generate_board(
                    new_game_input.generation_settings
                )

            gameplay = game.Gameplay(
                user_id=user.id if user else None,
                board_id=board.id,
            )

            gameplay = await self.game_repo.add_gameplay(gameplay)
            return NewGameOutput(gameplay_id=gameplay.id, board_id=board.id)

        except BoardNotFoundException:
            raise BoardNotExists(
                f"Board with id {new_game_input.board_id} does not exist"
            ) from None

    async def get_gameplays(self, user: CurrentUser, pagination_params: Params):
        return await self.game_repo.get_gameplays(user.id, pagination_params)
