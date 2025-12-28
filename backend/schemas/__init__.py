from abc import ABC, abstractmethod
from typing import Any, Self

from pydantic import BaseModel, ConfigDict


class Response(ABC, BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: (
            "type" if field_name == "ws_type" else field_name
        ),
    )

    @classmethod
    @abstractmethod
    def build(cls, *args: Any) -> Self: ...

    @classmethod
    def create(cls, data: Any, *, include_ws_type: bool = True) -> str:
        exclude = set() if include_ws_type else {"ws_type"}
        instance = cls.build(*data) if isinstance(data, tuple) else cls.build(data)
        return instance.model_dump_json(exclude=exclude, by_alias=True)
