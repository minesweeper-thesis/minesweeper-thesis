from typing import Annotated

from fastapi import Depends

from backend import repositories
from backend.core.game import *
from backend.repositories.exceptions import *
from backend.services.exceptions import *

GameRepository = Annotated[repositories.SingleplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]


class MultiplayerService:
    def __init__(
        self,
        board_repo: BoardRepository,
        game_repo: GameRepository,
    ):
        self.game_repo = game_repo
        self.board_repo = board_repo
        self.gameplay = None
        self.gameplay_id = None
        self.game_over = False
