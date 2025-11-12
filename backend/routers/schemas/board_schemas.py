from typing import Optional

from pydantic import BaseModel, Field

from backend.core.board import GenerationSettings, GeneratorSettings, GeneratorType


class GenerationRequest(BaseModel):
    type: GeneratorType
    settings: Optional[GeneratorSettings] = Field(
        None, description="Required if generator_type is set to 'ml'"
    )

    def to_generation_settings(self) -> GenerationSettings:
        return GenerationSettings(
            type=self.type,
            settings=self.settings,
        )
