from abc import ABC
from typing import Protocol

from backend.core.game import *
from backend.services.dto.game_action_results import *


class GameAction(Protocol):
    def execute(self, gameplay: Gameplay) -> "GameActionResult": ...


class GameCellAction(GameAction, ABC):
    cell: Cell

    def __init__(self, cell: Cell):
        self.cell = cell


class RevealOneAction(GameCellAction):
    def execute(self, gameplay: Gameplay) -> RevealResult:
        gameplay.reveal_one(self.cell)
        return RevealResult(
            revealed_cells=gameplay.get_game_state().revealed_cells,
            game_status=gameplay.get_game_state().status,
        )


class RevealManyAction(GameCellAction):
    def execute(self, gameplay: Gameplay) -> RevealResult:
        gameplay.reveal_many(self.cell)
        return RevealResult(
            revealed_cells=gameplay.get_game_state().revealed_cells,
            game_status=gameplay.get_game_state().status,
        )


class FlagAction(GameCellAction):
    def execute(self, gameplay: Gameplay) -> FlagResult:
        gameplay.flag(self.cell)
        return FlagResult(game_status=gameplay.get_game_state().status)


class RemoveFlagAction(GameCellAction):
    def execute(self, gameplay: Gameplay) -> RemoveFlagResult:
        gameplay.remove_flag(self.cell)
        return RemoveFlagResult(game_status=gameplay.get_game_state().status)


class UseHintAction(GameAction):
    def execute(self, gameplay: Gameplay) -> HintResult:
        hint_cell = gameplay.use_hint()
        safe_cells = [hint_cell] if hint_cell else []
        return HintResult(
            safe_cells=safe_cells, game_status=gameplay.get_game_state().status
        )


__all__ = [
    "RevealOneAction",
    "RevealManyAction",
    "FlagAction",
    "RemoveFlagAction",
    "UseHintAction",
    "GameAction",
]
