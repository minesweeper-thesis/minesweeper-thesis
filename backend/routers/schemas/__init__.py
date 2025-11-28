import inspect
from abc import ABC, abstractmethod
from typing import (
    Annotated,
    Any,
    ClassVar,
    Self,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, ConfigDict, Discriminator, Tag, TypeAdapter


def match_annotation(value: Any, ann: Any) -> bool:
    if ann is inspect._empty:
        return False

    origin = get_origin(ann)
    args = get_args(ann)

    if origin is Annotated and args:
        return match_annotation(value, args[0])

    if origin is Union:
        return any(match_annotation(value, arg) for arg in args)

    if origin is list and args:
        return isinstance(value, list) and all(
            match_annotation(x, args[0]) for x in value
        )

    if origin is dict and len(args) == 2:
        return isinstance(value, dict) and all(
            match_annotation(k, args[0]) and match_annotation(v, args[1])
            for k, v in value.items()
        )

    if origin is tuple and args:
        if not isinstance(value, tuple):
            return False
        if len(args) == 2 and args[1] is Ellipsis:
            return all(match_annotation(x, args[0]) for x in value)
        return len(value) == len(args) and all(
            match_annotation(x, a) for x, a in zip(value, args)
        )

    try:
        return isinstance(value, ann)
    except TypeError:
        return False


def match_params(data: Any, ann_list: list[Any]) -> bool:
    if not ann_list:
        return False

    if len(ann_list) == 1:
        return match_annotation(data, ann_list[0])

    if not isinstance(data, tuple) or len(data) != len(ann_list):
        return False

    return all(match_annotation(val, ann) for val, ann in zip(data, ann_list))


class Response(ABC, BaseModel):
    _registry: ClassVar[list[type[Self]]] = []

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: (
            "type" if field_name == "ws_type" else field_name
        ),
    )

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            cls._registry.append(cls)

    @classmethod
    @abstractmethod
    def from_core(cls, *args: Any) -> Self: ...

    @classmethod
    def create(cls, data: Any, *, include_ws_type: bool = True) -> str:
        exclude = set() if include_ws_type else {"ws_type"}

        for response_cls in cls._registry:
            type_hints = get_type_hints(response_cls.from_core)
            sig = inspect.signature(response_cls.from_core)
            params = [p for p in sig.parameters.values() if p.name != "cls"]
            ann_list = [type_hints.get(p.name, p.annotation) for p in params]

            if match_params(data, ann_list):
                instance = (
                    response_cls.from_core(*data)
                    if isinstance(data, tuple)
                    else response_cls.from_core(data)
                )
                return instance.model_dump_json(exclude=exclude, by_alias=True)

        raise ValueError(f"Unknown data type: {type(data)}")


class Request(ABC, BaseModel):
    _registry: ClassVar[list[type[Self]]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls) and "ws_type" in cls.__dict__:
            cls._registry.append(cls)

    @abstractmethod
    def to_core(self) -> Any: ...

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
        return request.to_core()
