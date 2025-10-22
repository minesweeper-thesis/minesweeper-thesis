import uuid
from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator

from backend.schemas.board import *


class NewGameInput(BaseModel):
    board_id: Optional[uuid.UUID] = Field(
        None, description="One of board_id or generation_settings must be provided"
    )
    generation_settings: Optional[GenerationInput] = Field(
        None, description="One of board_id or generation_settings must be provided"
    )

    @model_validator(mode="after")
    def validate(self) -> Self:
        board_id = self.board_id
        generation_settings = self.generation_settings

        if board_id is not None and generation_settings is not None:
            raise ValueError(
                "Only one of board_id or generation_settings can be provided, not both."
            )

        return self


class NewGameOutput(BaseModel):
    gameplay_id: uuid.UUID
