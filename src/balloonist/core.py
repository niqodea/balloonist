from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import NoneType, UnionType
from typing import (
    Mapping,
    Protocol,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from balloonist.utils import FrozenDict

BasicType = int | float | str | bool
"""
The type alias for JSON basic types.
"""

B = TypeVar("B", bound=BasicType)


@dataclass(frozen=True)
class Struct:
    """
    The base class for structs.
    """

    pass


@dataclass(frozen=True)
class NamedStruct(Struct):
    """
    The marker class for named structs.
    """

    name: str
    """
    The name of the struct.
    """


S = TypeVar("S", bound=Struct)
NS = TypeVar("NS", bound=NamedStruct)

J = TypeVar("J", bound="Json")
Json: TypeAlias = dict[str, J] | list[J] | B | None
"""
Value that can be dumped to JSON format.
"""

F = TypeVar("F", bound="Field")
Field: TypeAlias = FrozenDict[S, F] | tuple[F, ...] | frozenset[F] | S | B | None
"""
Field of a struct.
"""


class FieldDeflator:
    """
    Deflates struct fields to their JSON representations.
    """

    def __init__(
        self,
        storers: Mapping[type[NamedStruct], StructStorer[NamedStruct]],
        base_types: Mapping[type[NamedStruct], type[Struct]],
    ) -> None:
        """
        :param storers: The storers of named structs.
        :param base_types: The base types indexed by the corresponding named types.
        """
        self._storers = storers
        self._base_types = base_types

    def deflate(self, value: Field) -> Json:
        """
        Deflate a field to its JSON representation.

        :param value: The field to deflate.
        :return: The JSON representation of the field.
        """
        if isinstance(value, Struct):
            if isinstance(value, NamedStruct):
                storers = self._storers[value.__class__]
                storers.store(value)

                named_type = value.__class__
                base_type = self._base_types[named_type]

                return {
                    "type": base_type.__qualname__,
                    "name": value.name,
                }
            else:
                base_type = value.__class__
                fields = {
                    field_name: self.deflate(field)
                    for field_name, field in value.__dict__.items()
                }
                return {
                    "type": base_type.__qualname__,
                    "fields": fields,
                }

        if isinstance(value, FrozenDict):
            return {
                self._deflate_key(key): self.deflate(value)
                for key, value in value.items()
            }

        if isinstance(value, (tuple, frozenset)):
            return [self.deflate(item) for item in value]

        if isinstance(value, BasicType):  # type: ignore[arg-type,misc]
            return value

        if value is None:
            return None

        raise ValueError(f"Unsupported type: {type(value)}")

    # Since the dict representation of a struct is not suitable as a json key,
    # we have an ad-hoc method to turn it into a string
    # TODO: Maybe also include str keys (will need to update the spec for Field)
    def _deflate_key(self, key: Struct) -> str:
        # NOTE: the type ignore could be avoided by having an ad-hoc deflate_struct
        json_: dict[str, Json] = self.deflate(key)  # type: ignore[assignment]

        type_ = json_["type"]

        if (name := json_.get("name")) is not None:
            return f"n:{type_}:{name}"

        if (fields := json_.get("fields")) is not None:
            fields_str = json.dumps(fields)
            return f"a:{type_}:{fields_str}"  # a stands for anonymous

        raise RuntimeError("`deflate` method returned invalid JSON")


class FieldInflator:
    """
    Inflates fields from their JSON representations.
    """

    def __init__(
        self,
        base_types: Mapping[str, type[Struct]],
        named_types: Mapping[type[Struct], type[NamedStruct]],
        providers: Mapping[type[NamedStruct], StructProvider[NamedStruct]],
    ) -> None:
        """
        :param base_types: Base types indexed by their qualified names.
        :param named_types: Named types indexed by the corresponding base types.
        :param providers: The providers of named structs.
        """
        self._base_types = base_types
        self._named_types = named_types
        self._providers = providers

    def inflate(self, json_: Json, static_type: type[F]) -> F:
        """
        Inflate a field from its JSON representation.

        :param deflated_field: The JSON representation of the field.
        :param static_type: The static type of the field.
        :return: The inflated field.
        """
        type_origin = get_origin(static_type)
        type_args = get_args(static_type)

        if type_origin is FrozenDict:
            assert isinstance(json_, dict)
            key_type, value_type = type_args
            return FrozenDict(
                {
                    self._inflate_key(key, key_type): self.inflate(value, value_type)
                    for key, value in json_.items()
                }
            )  # type: ignore[return-value]

        if type_origin is tuple:
            assert isinstance(json_, list)
            (item_type,) = type_args
            return tuple(self.inflate(item, item_type) for item in json_)  # type: ignore[return-value]

        if type_origin is frozenset:
            assert isinstance(json_, list)
            (item_type,) = type_args
            return frozenset(self.inflate(item, item_type) for item in json_)  # type: ignore[return-value]

        if type_origin is UnionType:
            # NOTE: Arbitrary union types not implemented for now
            # They would either require a try/except logic or inspecting the deflated
            # field to determine the type
            optional_type, none_type = type_args
            assert none_type is NoneType

            if json_ is None:
                return None  # type: ignore[return-value]

            return self.inflate(json_, optional_type)

        if issubclass(static_type, Struct):
            assert isinstance(json_, dict)
            base_type_name = json_["type"]
            base_type = self._base_types[base_type_name]
            assert issubclass(base_type, static_type)

            if (name := json_.get("name")) is not None:
                named_type = self._named_types[base_type]
                provider = self._providers[named_type]
                return provider.get(name)  # type: ignore[return-value]

            if (fields := json_.get("fields")) is not None:
                field_types = get_type_hints(base_type)
                fields = {
                    field_name: self.inflate(
                        field_json,
                        field_types[field_name],
                    )
                    for field_name, field_json in fields.items()
                }

                return base_type(**fields)  # type: ignore[return-value]

        if issubclass(static_type, BasicType):  # type: ignore[arg-type,misc]
            assert isinstance(json_, static_type)
            return json_  # type: ignore[return-value]

        raise ValueError(f"Unsupported type: {static_type}")

    def _inflate_key(self, key: str, static_type: type[S]) -> S:
        dict_type, _, dict_content = key.partition(":")

        match dict_type:
            case "n":
                type_, _, name = dict_content.partition(":")
                dict_ = {
                    "type": type_,
                    "name": name,
                }
                return self.inflate(dict_, static_type)
            case "a":
                type_, _, fields_str = dict_content.partition(":")
                fields = json.loads(fields_str)
                dict_ = {
                    "type": type_,
                    "fields": fields,
                }
                return self.inflate(dict_, static_type)
            case _:
                raise ValueError(f"Unsupported dict type: {dict_type}")


# NOTE: Ignoring mypy misc below as it otherwise complains that NM must be covariant
class StructHandler(Protocol[NS]):  # type: ignore[misc]
    """
    Handles named structs.
    """

    def get_type(self) -> type[NS]:
        """
        :return: The type of the structs handled by this handler.
        """


class StructProvider(StructHandler[NS], Protocol[NS]):  # type: ignore[misc]
    """
    Provides named structs.
    """

    def get(self, name: str) -> NS:
        """
        Provide a named struct.

        :param name: The name of the struct.
        :return: The struct.
        """


class StructStorer(StructHandler[NS], Protocol[NS]):
    """
    Stores named structs.
    """

    def store(self, struct: NS) -> None:
        """
        Store a named struct.

        :param struct: The struct to store.
        """


class Balloonist(StructProvider[NS], StructStorer[NS]):
    """
    Manages named structs.
    """

    def __init__(
        self,
        type_: type[NS],
        inflator: FieldInflator,
        deflator: FieldDeflator,
        jsons_path: Path,
    ) -> None:
        """
        :param type_: The type of the managed structs.
        :param inflator: The inflator of fields.
        :param deflator: The deflator of fields.
        :param jsons_path: The directory containing the JSON representations of the
            structs.
        """
        self._type = type_
        self._deflator = deflator
        self._inflator = inflator
        self._jsons_path = jsons_path

        self._structs: dict[str, NamedStruct] = {}

    def get_type(self) -> type[NS]:
        return self._type

    def get(self, name: str) -> NS:
        if (value := self._structs.get(name)) is not None:
            return value  # type: ignore[return-value]

        json_path = self._jsons_path / f"{name}.json"
        json_ = json.loads(json_path.read_text())

        field_types = get_type_hints(self._type)
        init_kwargs = {"name": name} | {
            field_name: self._inflator.inflate(
                json_=deflated_field,
                static_type=field_types[field_name],
            )
            for field_name, deflated_field in json_.items()
        }

        struct = self._type(**init_kwargs)
        self._structs[name] = struct
        return struct

    def store(self, struct: NS) -> None:
        if (existing := self._structs.get(struct.name)) is not None:
            assert struct is existing
            return

        self._structs[struct.name] = struct

        fields = {n: v for n, v in struct.__dict__.items()}
        fields.pop("name")

        json_ = {
            field_name: self._deflator.deflate(field)
            for field_name, field in fields.items()
        }

        json_path = self._jsons_path / f"{struct.name}.json"
        json_path.write_text(json.dumps(json_, indent=2))


class BalloonistProvider:
    """
    Provides balloonists for types of structs.
    """

    def __init__(
        self,
        balloonists: Mapping[type[NamedStruct], Balloonist[NamedStruct]],
    ) -> None:
        """
        :param balloonists: The balloonists for types of structs.
        """
        self._balloonists = balloonists

    def get(self, type_: type[NS]) -> Balloonist[NS]:
        """
        Provides a balloonist for a type of structs.

        :param type_: A type of structs.
        :return: The balloonist for the type of structs.
        """
        if (balloonist := self._balloonists.get(type_)) is not None:
            return balloonist  # type: ignore[return-value]

        raise ValueError(f"Unsupported type: {type_}")

    @staticmethod
    def create(
        base_types: set[type[Struct]],
        named_types: Mapping[type[Struct], type[NamedStruct]],
        jsons_root: Path,
    ) -> BalloonistProvider:
        """
        Create a provider of balloonists for types of structs.

        :param base_types: The base types of structs.
        :param named_types: Named types indexed by the corresponding base types.
        :param jsons_root: The root containing the JSON representations of the
            named structs, with each type of structs having its own directory.
        :return: The provider of balloonists for types of structs.
        """
        balloonists: dict[type[NamedStruct], Balloonist[NamedStruct]] = {}

        field_deflator = FieldDeflator(
            storers=balloonists,
            base_types={v: k for k, v in named_types.items()},
        )
        field_inflator = FieldInflator(
            base_types={t.__qualname__: t for t in base_types},
            named_types=named_types,
            providers=balloonists,
        )
        for base_type, named_type in named_types.items():
            jsons_path = jsons_root / base_type.__qualname__
            jsons_path.mkdir(exist_ok=True)
            balloonists[named_type] = Balloonist(
                type_=named_type,
                inflator=field_inflator,
                deflator=field_deflator,
                jsons_path=jsons_path,
            )

        return BalloonistProvider(
            balloonists={t: balloonists[t] for t in named_types.values()}
        )
