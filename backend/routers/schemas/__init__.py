import inspect
from abc import ABC, abstractmethod
from typing import Annotated, Any, ClassVar, Self, Union

from pydantic import BaseModel, ConfigDict, Discriminator, Tag, TypeAdapter


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


class WSRequest(ABC, BaseModel):
    _registry: ClassVar[list[type[Self]]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls) and "ws_type" in cls.__dict__:
            cls._registry.append(cls)

    @abstractmethod
    def parse(self) -> Any: ...

    @classmethod
    def from_dict(cls, data: dict) -> Any:
        if isinstance(data, dict) and "type" in data:
            data["ws_type"] = data.pop("type")

        union_types = tuple(
            Annotated[action_cls, Tag(action_cls.model_fields["ws_type"].default)]
            for action_cls in cls._registry
        )

        adapter = TypeAdapter(Annotated[Union[union_types], Discriminator("ws_type")])  # type: ignore[var-annotated]
        request = adapter.validate_python(data)
        return request.parse()
