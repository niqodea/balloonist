from __future__ import annotations

import json
from dataclasses import dataclass, make_dataclass
from enum import Enum
from pathlib import Path
from types import NoneType, UnionType
from typing import (
    ClassVar,
    Generic,
    Mapping,
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from typing_extensions import dataclass_transform


@dataclass(frozen=True)
class Balloon:
    """
    The top class for balloons.
    """

    def to_named(self, name: str) -> Self:
        """
        Promote the balloon to a named balloon.

        :param name: The name of the balloon.
        :return: The named balloon.
        """
        if isinstance(self, NamedBalloon):
            raise ValueError(f"Balloon is already named: {self}")
        named_type = type(self).Named
        return named_type(name=name, **self.__dict__)  # type: ignore[return-value]

    def as_named(self) -> NamedBalloon:
        """
        Treat the balloon as a named balloon.
        """
        assert isinstance(self, NamedBalloon)
        return self

    Named: ClassVar[type[NamedBalloon]]
    """
    The named type of the balloon class.
    """


# Ref: https://stackoverflow.com/questions/53990296
@dataclass(frozen=True, eq=False)
class NamedBalloon(Balloon):
    """
    The marker class for named balloons.
    """

    name: str
    """
    The name of the balloon.
    """

    def __hash__(self) -> int:
        return hash(f"{type(self).Base.__qualname__}:{self.name}")

    Base: ClassVar[type[Balloon]]
    """
    The base type of the named balloon class.
    """


@dataclass_transform(frozen_default=True)
def balloon(cls: type[Balloon]) -> type[Balloon]:
    """
    Decorator required to correctly setup balloon classes.
    """

    cls = dataclass(frozen=True)(cls)

    if issubclass(cls, NamedBalloon):
        # It makes sense to define some classes as only having named instances
        # It also enables safe usage of instances as dictionary keys
        named_cls = cls
    else:
        named_cls = make_dataclass(
            cls_name=f"{cls.__name__}.Named",
            fields=[],
            bases=(NamedBalloon, cls),
            frozen=True,
            eq=False,
        )

    cls.Named = named_cls
    named_cls.Base = cls

    return cls


BasicType = int | float | str | bool
"""
The type alias for JSON basic types.
"""

BL = TypeVar("BL", bound=Balloon)
BLN = TypeVar("BLN", bound=NamedBalloon)
E = TypeVar("E", bound=Enum)
BT = TypeVar("BT", bound=BasicType)

F = TypeVar("F", bound="Field")
Field: TypeAlias = (
    None
    | dict[BLN, F]
    | dict[E, F]
    | dict[str, F]
    | set[BLN]
    | set[E]
    | set[str]
    | tuple[F, ...]
    | BL
    | E
    | BT
)
"""
Field of a balloon.
"""

J = TypeVar("J", bound="Json")
Json: TypeAlias = dict[str, J] | list[J] | BT | None
"""
Value that can be dumped to JSON format.
"""


class FieldDeflator:
    """
    Deflates balloon fields to their JSON representations.
    """

    def __init__(
        self,
        trackers: Mapping[type[Balloon], BalloonTracker[NamedBalloon]],
    ) -> None:
        """
        :param trackers: The trackers of named balloons.
        """
        self._trackers = trackers

    def deflate(self, value: Field) -> Json:
        """
        Deflate a field to its JSON representation.

        :param value: The field to deflate.
        :return: The JSON representation of the field.
        """
        if isinstance(value, Balloon):
            if isinstance(value, NamedBalloon):
                named_type = value.__class__
                tracker = self._trackers[named_type.Base]
                tracker.track(value)
                return f"{named_type.Base.__qualname__}:{value.name}"
            else:
                type_ = value.__class__
                fields = {
                    field_name: self.deflate(field)
                    for field_name, field in value.__dict__.items()
                }
                return {
                    "type": type_.__qualname__,
                    "fields": fields,
                }
            raise ValueError(f"Unsupported balloon type: {type(value)}")

        if isinstance(value, dict):
            return {
                self.deflate(key): self.deflate(value) for key, value in value.items()
            }

        if isinstance(value, (set, tuple)):
            return [self.deflate(item) for item in value]

        if isinstance(value, Enum):
            return f"{value.name}"

        if isinstance(value, BasicType):  # type: ignore[arg-type,misc]
            return value

        if value is None:
            return None

        raise ValueError(f"Unsupported type: {type(value)}")


class FieldInflator:
    """
    Inflates fields from their JSON representations.
    """

    def __init__(
        self,
        types_: dict[str, type[Balloon]],
        providers: Mapping[type[Balloon], BalloonProvider[NamedBalloon]],
    ) -> None:
        """
        :param types: The balloon types, indexed by their name.
        :param providers: The providers of named balloons.
        """
        self._types = types_
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

        if type_origin is dict:
            assert isinstance(json_, dict)
            key_type, value_type = type_args
            return {
                self.inflate(key, key_type): self.inflate(value, value_type)
                for key, value in json_.items()
            }  # type: ignore[return-value]

        if type_origin is tuple:
            assert isinstance(json_, list)
            (item_type,) = type_args
            return tuple(self.inflate(item, item_type) for item in json_)  # type: ignore[return-value]

        if type_origin is set:
            assert isinstance(json_, list)
            (item_type,) = type_args
            return {self.inflate(item, item_type) for item in json_}  # type: ignore[return-value]

        if type_origin is UnionType:
            # NOTE: Arbitrary union types not implemented for now
            # They would either require a try/except logic or inspecting the deflated
            # field to determine the type
            optional_type, none_type = type_args
            assert none_type is NoneType

            if json_ is None:
                return None  # type: ignore[return-value]

            return self.inflate(json_, optional_type)

        if issubclass(static_type, Balloon):
            if isinstance(json_, str):
                # it is a named balloon
                type_name, _, name = json_.partition(":")
                type_ = self._types[type_name]
                assert issubclass(type_, static_type)
                provider = self._providers[type_]
                return provider.get(name)  # type: ignore[return-value]
            if isinstance(json_, dict):
                type_name = json_["type"]
                type_ = self._types[type_name]
                assert issubclass(type_, static_type)
                fields = json_["fields"]
                field_types = get_type_hints(type_)
                fields = {
                    field_name: self.inflate(
                        field_json,
                        field_types[field_name],
                    )
                    for field_name, field_json in fields.items()
                }
                return type_(**fields)  # type: ignore[return-value]
            raise ValueError(f"Unsupported balloon json: {json_}")

        if issubclass(static_type, Enum):
            assert isinstance(json_, str)
            return static_type[json_]  # type: ignore[return-value]

        if issubclass(static_type, BasicType):  # type: ignore[arg-type,misc]
            assert isinstance(json_, static_type)
            return json_  # type: ignore[return-value]

        raise ValueError(f"Unsupported type: {static_type}")


# NOTE: Ignoring mypy misc below as it otherwise complains that NM must be covariant


class BalloonProvider(Protocol[BLN]):  # type: ignore[misc]
    """
    Provides named balloons of a balloon type, not including subtypes.
    """

    def get(self, name: str) -> BLN:
        """
        Provide a named balloon.

        :param name: The name of the balloon.
        :return: The balloon.
        """


class BalloonTracker(Protocol[BLN]):  # type: ignore[misc]
    """
    Tracks named balloons of a balloon type, not including subtypes.
    """

    def track(self, balloon: BLN) -> None:
        """
        Track a named balloon.

        :param balloon: The balloon to track.
        """


class BalloonSpecialist(BalloonProvider[BLN], BalloonTracker[BLN]):
    """
    Manages named balloons of a balloon type, not including subtypes.
    """

    def __init__(
        self,
        type_: type[BLN],
        names: set[str],
        inflator: FieldInflator,
        deflator: FieldDeflator,
        jsons_path: Path,
    ) -> None:
        """
        :param type_: The type of the managed balloons.
        :param names: The names of the balloons.
        :param inflator: The inflator of fields.
        :param deflator: The deflator of fields.
        :param jsons_path: The directory containing the JSON representations of the
            balloons.
        """
        self._type = type_
        self._names = names
        self._deflator = deflator
        self._inflator = inflator
        self._jsons_path = jsons_path

        self._balloons: dict[str, NamedBalloon] = {}

    def get(self, name: str) -> BLN:
        if name not in self._names:
            raise ValueError(f"Could not find balloon with name: {name}")

        if (value := self._balloons.get(name)) is not None:
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

        balloon = self._type(**init_kwargs)
        self._balloons[name] = balloon
        return balloon

    def track(self, balloon: BLN) -> None:
        if type(balloon) is not self._type:
            raise ValueError(f"Could not handle type: {type(balloon)}")

        if (tracked_balloon := self._balloons.get(balloon.name)) is not None:
            assert balloon is tracked_balloon
            return

        if balloon.name in self._names:
            stored_balloon = self.get(balloon.name)
            assert balloon == stored_balloon
            # We keep track of the input balloon to only have one object around
            self._balloons[balloon.name] = balloon
            return

        fields = {n: v for n, v in balloon.__dict__.items()}
        fields.pop("name")
        json_ = {
            field_name: self._deflator.deflate(field)
            for field_name, field in fields.items()
        }

        json_path = self._jsons_path / f"{balloon.name}.json"
        json_path.write_text(json.dumps(json_, indent=2))

        self._names.add(balloon.name)
        self._balloons[balloon.name] = balloon

    def get_names(self) -> set[str]:
        """
        Provide the names of the managed balloons.

        :return: The names of the managed balloons.
        """
        return self._names


class NamespaceManager:
    """
    Efficiently manages the namespace of balloon types.
    """

    def __init__(
        self,
        top_namespace_types: set[type[Balloon]],
    ) -> None:
        """
        :param top_namespace_types: The balloon types that define the top of their
            respective namespaces.
        """
        self._top_namespace_types = top_namespace_types
        self._name_to_types: dict[str, set[type[Balloon]]] = {}

    def get(self, name: str, namespace_type: type[BL]) -> type[BL] | None:
        """
        Provide the type of the balloon with the given name, if any.

        :param name: The balloon name.
        :param namespace_type: The namespace type to use to find the balloon type.
        :return: The type of the balloon, if any.
        """
        if all(not issubclass(namespace_type, t) for t in self._top_namespace_types):
            raise ValueError(f"Unsupported namespace type: {namespace_type}")

        types_ = self._name_to_types.get(name, set())

        candidate_types = {t for t in types_ if issubclass(t, namespace_type)}

        if len(candidate_types) == 0:
            return None

        if len(candidate_types) > 1:
            raise ValueError(f"Found multiple balloons with name: {name}")

        type_ = candidate_types.pop()
        return type_

    def track(self, name: str, type_: type[Balloon]) -> None:
        """
        Track a balloon by name and type.

        :param name: The balloon name.
        :param type_: The balloon type.
        """
        if name not in self._name_to_types:
            self._name_to_types[name] = set()

        if type_ in self._name_to_types[name]:
            return

        relevant_namespace_types = {
            t for t in self._top_namespace_types if issubclass(type_, t)
        }
        for tracked_type in self._name_to_types[name]:
            for namespace_type in relevant_namespace_types:
                if issubclass(tracked_type, namespace_type):
                    raise ValueError(
                        "Found balloon with same name in same namespace.\n"
                        f"Name: {name}\n"
                        f"Namespace type: {namespace_type}\n"
                        f"Existing type: {tracked_type}\n"
                        f"New type: {type_}"
                    )

        self._name_to_types[name].add(type_)


class Balloonist(Generic[BL]):
    """
    Manages named balloons of a balloon type, including subtypes.
    """

    def __init__(
        self,
        type_: type[BL],
        namespace_manager: NamespaceManager,
        balloon_specialists: dict[type[Balloon], BalloonSpecialist[NamedBalloon]],
    ) -> None:
        """
        :param type_: The type of the managed balloons.
        :param name_to_type_manager: The manager to retrieve balloon types by name.
        :param balloon_specialists: The managers of the balloons.
        """
        self._type = type_
        self._namespace_manager = namespace_manager
        self._balloon_specialists = balloon_specialists

    def get(self, name: str) -> BL:
        """
        Provide the balloon with the given name, possibly inflating it from the JSON
        database if missing from memory.

        :param name: The balloon name.
        :return: The balloon.
        """
        type_: type[Balloon] | None = self._namespace_manager.get(name, self._type)
        if type_ is None:
            raise ValueError(f"Could not find balloon with name: {name}")

        balloon_specialist = self._balloon_specialists[type_]  # type: ignore[index]
        return balloon_specialist.get(name)  # type: ignore[return-value]

    def track(self, balloon: BL) -> None:
        """
        Track a balloon, possibly deflating it to the JSON database if missing from
        disk.

        :param balloon: The balloon to track.
        """
        assert isinstance(balloon, NamedBalloon)
        named_type = type(balloon)
        type_ = named_type.Base

        tracked_type: type[Balloon] | None = self._namespace_manager.get(
            balloon.name, self._type
        )
        if tracked_type is not None:
            assert type_ is tracked_type

        balloon_specialist = self._balloon_specialists[type_]
        balloon_specialist.track(balloon)
        self._namespace_manager.track(balloon.name, type_)

    def get_names(self) -> set[str]:
        """
        Provide the names of the managed balloons.

        :return: The names of the managed balloons.
        """
        names = set()
        for balloon_specialist in self._balloon_specialists.values():
            names.update(balloon_specialist.get_names())
        return names


class BalloonistFactory(Generic[BL]):
    """
    Factory for balloonists.
    """

    def __init__(
        self,
        namespace_types: set[type[Balloon]],
        balloon_specialists: dict[type[Balloon], BalloonSpecialist[NamedBalloon]],
        namespace_manager: NamespaceManager,
    ) -> None:
        """
        :param namespace_types: The balloon types representing a namespace.
        :param balloon_specialists: The balloon_specialists for types of balloons.
        :param namespace_manager: The manager of the namespaces of balloons.
        """
        self._namespace_types = namespace_types
        self._balloon_specialists = balloon_specialists
        self._namespace_manager = namespace_manager

    def instantiate(self, type_: type[BL]) -> Balloonist[BL]:
        """
        Instantiate a balloonist for a balloon type

        :param type_: A balloon type.
        :return: The balloonist for the balloon type.
        """
        if all(not issubclass(type_, t) for t in self._namespace_types):
            raise ValueError(f"Unsupported balloonist balloon type: {type_}")

        balloon_specialists: dict[type[Balloon], BalloonSpecialist[NamedBalloon]] = {
            t: bs for t, bs in self._balloon_specialists.items() if issubclass(t, type_)
        }

        return Balloonist(
            type_=type_,
            namespace_manager=self._namespace_manager,
            balloon_specialists=balloon_specialists,
        )

    @staticmethod
    def create(
        top_namespace_types: set[type[Balloon]],
        types_: set[type[Balloon]],
        json_database_path: Path,
    ) -> BalloonistFactory:
        """
        Create a factory for balloonists.

        :param top_namespace_types: The balloon types that define the top of their
            respective namespaces.
        :param types_: The balloon types.
        :param json_database_path: The path to the JSON database.
        :return: The factory for balloonists.
        """
        balloon_specialists: dict[type[Balloon], BalloonSpecialist[NamedBalloon]] = {}

        field_deflator = FieldDeflator(
            trackers=balloon_specialists,
        )
        field_inflator = FieldInflator(
            types_={t.__qualname__: t for t in types_},
            providers=balloon_specialists,
        )
        for type_ in types_:
            if not any(issubclass(type_, t) for t in top_namespace_types):
                continue
            jsons_path = json_database_path / type_.__qualname__
            jsons_path.mkdir(exist_ok=True)
            names = {p.stem for p in jsons_path.iterdir()}
            balloon_specialists[type_] = BalloonSpecialist(
                type_=type_.Named,
                names=names,
                inflator=field_inflator,
                deflator=field_deflator,
                jsons_path=jsons_path,
            )

        namespace_manager = NamespaceManager(top_namespace_types=top_namespace_types)
        for type_, balloon_specialist in balloon_specialists.items():
            for name in balloon_specialist.get_names():
                namespace_manager.track(name, type_)

        return BalloonistFactory(
            namespace_types=top_namespace_types,
            balloon_specialists=balloon_specialists,
            namespace_manager=namespace_manager,
        )
