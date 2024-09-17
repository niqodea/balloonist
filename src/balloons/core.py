from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, make_dataclass
from enum import Enum
from pathlib import Path
from types import NoneType, UnionType
from typing import (
    ClassVar,
    Generic,
    Mapping,
    NoReturn,
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


Atomic = int | float | str | bool
"""
The type alias for atomic types.
"""

B = TypeVar("B", bound=Balloon)
BN = TypeVar("BN", bound=NamedBalloon)
E = TypeVar("E", bound=Enum)
A = TypeVar("A", bound=Atomic)

VI = TypeVar("VI", bound="InflatedValue")
InflatedValue: TypeAlias = (
    None
    | dict[BN, VI]
    | dict[E, VI]
    | dict[str, VI]
    | set[BN]
    | set[E]
    | set[str]
    | tuple[VI, ...]
    | B
    | E
    | A
)
"""
Value that can be deflated.
"""

VD = TypeVar("VD", bound="DeflatedValue")
DeflatedValue: TypeAlias = dict[str, VD] | list[VD] | A | None
"""
Value that can be inflated or dumped to JSON.
"""



class Inflator:
    """
    Inflates values from their JSON representations.
    """

    def __init__(
        self,
        types_: dict[str, type[Balloon]],
        providers: Mapping[type[Balloon], SpecializedBalloonProvider[NamedBalloon]],
    ) -> None:
        """
        :param types: The balloon types, indexed by their name.
        :param providers: The providers of named balloons.
        """
        self._types = types_
        self._providers = providers

    def inflate(self, deflated_value: DeflatedValue, static_type: type[VI]) -> VI:
        """
        Inflate a deflated value.

        :param value: The deflated value.
        :param static_type: The static type of the value.
        :return: The inflated value.
        """
        type_origin = get_origin(static_type)
        type_args = get_args(static_type)

        if type_origin is dict:
            assert isinstance(deflated_value, dict)
            key_type, value_type = type_args
            return {
                self.inflate(key, key_type): self.inflate(value, value_type)
                for key, value in deflated_value.items()
            }  # type: ignore[return-value]

        if type_origin is tuple:
            assert isinstance(deflated_value, list)
            (item_type,) = type_args
            return tuple(self.inflate(item, item_type) for item in deflated_value)  # type: ignore[return-value]

        if type_origin is set:
            assert isinstance(deflated_value, list)
            (item_type,) = type_args
            return {self.inflate(item, item_type) for item in deflated_value}  # type: ignore[return-value]

        if type_origin is UnionType:
            # NOTE: Arbitrary union types not implemented for now
            # They would either require a try/except logic or inspecting the deflated
            # value to determine the type
            optional_type, none_type = type_args
            assert none_type is NoneType

            if deflated_value is None:
                return None  # type: ignore[return-value]

            return self.inflate(deflated_value, optional_type)

        if issubclass(static_type, Balloon):
            if isinstance(deflated_value, str):
                # it is a named balloon
                type_name, _, name = deflated_value.partition(":")
                type_ = self._types[type_name]
                assert issubclass(type_, static_type)
                provider = self._providers[type_]
                return provider.get(name)  # type: ignore[return-value]
            if isinstance(deflated_value, dict):
                type_name = deflated_value["type"]
                type_ = self._types[type_name]
                assert issubclass(type_, static_type)
                deflated_fields = deflated_value["fields"]
                field_types = get_type_hints(type_)
                inflated_fields = {
                    field_name: self.inflate(
                        deflated_field,
                        field_types[field_name],
                    )
                    for field_name, deflated_field in deflated_fields.items()
                }
                return type_(**inflated_fields)  # type: ignore[return-value]
            raise ValueError(f"Unsupported balloon value: {deflated_value}")

        if issubclass(static_type, Enum):
            assert isinstance(deflated_value, str)
            return static_type[deflated_value]  # type: ignore[return-value]

        if issubclass(static_type, Atomic):  # type: ignore[arg-type,misc]
            assert isinstance(deflated_value, static_type)
            return deflated_value  # type: ignore[return-value]

        raise ValueError(f"Unsupported type: {static_type}")


class Deflator:
    """
    Deflates values to their JSON representations.
    """

    def __init__(
        self,
        trackers: Mapping[type[Balloon], SpecializedBalloonTracker[NamedBalloon]],
    ) -> None:
        """
        :param trackers: The trackers of named balloons.
        """
        self._trackers = trackers

    def deflate(self, value: InflatedValue) -> DeflatedValue:
        """
        Deflate a value.

        :param value: The value to deflate.
        :return: The deflated representation of the value.
        """
        if isinstance(value, Balloon):
            if isinstance(value, NamedBalloon):
                named_type = value.__class__
                tracker = self._trackers[named_type.Base]
                tracker.track(value)
                return f"{named_type.Base.__qualname__}:{value.name}"
            else:
                type_ = value.__class__
                deflated_fields = {
                    field_name: self.deflate(inflated_field)
                    for field_name, inflated_field in value.__dict__.items()
                }
                return {
                    "type": type_.__qualname__,
                    "fields": deflated_fields,
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

        if isinstance(value, Atomic):  # type: ignore[arg-type,misc]
            return value

        if value is None:
            return None

        raise ValueError(f"Unsupported type: {type(value)}")


# NOTE: Ignoring mypy misc below as it otherwise complains that BLN must be covariant


class BalloonDatabaseCache(Generic[BN]):
    """
    Caches database information about balloons of a certain type.
    """

    def __init__(self, type_: type[BN], names: set[str]) -> None:
        """
        :param type_: The type of the managed balloons.
        :param names: The names of the balloons in the database.
        """
        self._type = type_
        self._names = names  # this is in fact another type of cache

        self._balloons: dict[str, BN] = {}

    def get_cached_names(self) -> set[str]:
        """
        Get the names of the cached balloons.
        """
        return set(self._balloons.keys())
    
    def get_all_names(self) -> set[str]:
        """
        Get the names of all balloons in the database.
        """
        return self._names

    def get(self, name: str) -> BN:
        """
        Get a balloon by name.

        :param name: The name of the balloon.
        """
        if name not in self._names:
            raise ValueError(f"Could not find balloon with name: {name}")

        return self._cached_balloons[name]

    def track(balloon: BN) -> None:
        """
        Track a balloon in the stand.

        :param balloon: The balloon to put.
        """
        if type(balloon) is not self._type:
            raise ValueError(f"Could not handle type: {type(balloon)}")

        if balloon.name in self._balloons:
            raise ValueError(f"Balloon already in cache: {balloon.name}")
        
        if balloon.name not in self._names:
            self._names.add(balloon.name)

        self._balloons[balloon.name] = balloon



class SpecializedBalloonProvider(Protocol[BN]):  # type: ignore[misc]
    """
    Provides named balloons of a certain type, not including subtypes.
    """

    def get(self, name: str) -> BN:
        """
        Provide a named balloon.

        :param name: The name of the balloon.
        :return: The balloon.
        """

    def get_names(self) -> set[str]:
        """
        Provide the names of the balloons.

        :return: The names of the balloons.
        """

    def get_type(self) -> type[BN]:
        """
        Provide the type of the balloons.

        :return: The type of the balloons.
        """


class EmptySpecializedBalloonProvider(SpecializedBalloonProvider[NoReturn]):
    """
    The specialized balloon provider with no balloons.
    """
    def get(self, name: str) -> NoReturn:
        raise ValueError(f"Could not find balloon with name: {name}")

    def get_names(self) -> set[str]:
        return set()
    
    def get_type(self) -> type[NoReturn]:
        return NoReturn



class StandardSpecializedBalloonProvider(SpecializedBalloonProvider[BN]):
    """
    The standard specialized balloon provider.
    """

    def __init__(
        self,
        type_: type[BN],
        jsons_path: Path,
        cache: BalloonDatabaseCache[BN],
        baseline_provider: SpecializedBalloonProvider[BN],
        inflator: Inflator,
    ) -> None:
        """
        :param type_: Type of the managed balloons.
        :param jsons_path: Directory with the JSONs of the balloons.
        :param cache: Cache of the balloons.
        :param baseline_provider: Provider of balloons to fall back to.
        :param inflator: Inflator of balloon fields.
        """
        self._type = type_
        self._jsons_path = jsons_path
        self._cache = cache
        self._baseline_provider = baseline_provider
        self._inflator = inflator

    def get(self, name: str) -> BN:
        if name not in self._cache.get_all_names():
            if self._baseline_provider is not None:
                return self._baseline_provider.get(name)
            else:
                raise ValueError(f"Could not find balloon with name: {name}")

        if name in self._cache.get_cached_names():
            return self._cache.get(name)

        json_path = self._jsons_path / f"{name}.json"
        json_ = json.loads(json_path.read_text())

        field_types = get_type_hints(self._type)
        init_kwargs = {"name": name} | {
            field_name: self._inflator.inflate(
                deflated_value=deflated_field,
                static_type=field_types[field_name],
            )
            for field_name, deflated_field in json_.items()
        }

        balloon = self._type(**init_kwargs)
        self._cache.track(balloon)
        return balloon

    def get_names(self) -> set[str]:
        return self._cache.get_all_names() | set(self._baseline_provider.get_names())

    def get_type(self) -> type[BN]:
        return self._type


class SpecializedBalloonTracker(Generic[BN]):
    """
    Tracks named balloons of a certain type, not including subtypes.
    """

    def __init__(
        self,
        type_: type[BN],
        jsons_path: Path,
        cache: BalloonDatabaseCache[BN],
        baseline_provider: SpecializedBalloonProvider[BN],
        inflator: Inflator,
        deflator: Deflator,
    ) -> None:
        """
        :param type_: Type of the managed balloons.
        :param jsons_path: Directory with the JSONs of the balloons.
        :param cache: Cache of the balloons.
        :param baseline_provider: Provider of balloons to fall back to.
        :param inflator: Inflator of balloon fields.
        :param deflator: Deflator of balloon fields.
        """
        self._type = type_
        self._jsons_path = jsons_path
        self._cache = cache
        self._baseline_provider = baseline_provider
        self._inflator = inflator
        self_deflator = deflator

    def track(self, balloon: BN) -> None:
        """
        Track a named balloon.

        :param balloon: The balloon to track.
        """
        if type(balloon) is not self._reference_provider.get_type():
            raise ValueError(f"Could not handle type: {type(balloon)}")

        if (existing_balloon := self._reference_provider.get(balloon.name)) is not None:
            if balloon == existing_balloon:
                return
            else:
                raise ValueError(
                    f"Found conflicting balloon with name: {balloon.name}\n"
                    f"Existing balloon: {existing_balloon}\n"
                    f"New balloon: {balloon}"
                )

        fields = {n: v for n, v in balloon.__dict__.items()}
        fields.pop("name")
        json_ = {
            field_name: self._deflator.deflate(field)
            for field_name, field in fields.items()
        }

        json_path = self._jsons_path / f"{balloon.name}.json"
        json_path.write_text(json.dumps(json_, indent=2))


class DynamicTypeProvider(Protocol):
    """
    Efficiently provides the dynamic type of a balloon by name and static type.
    """

    def get(self, name: str, static_type: type[B]) -> type[B] | None:
        """
        Provide the type of the balloon with a given name and static type.

        :param name: Name of the balloon.
        :param static_type: Static type of the balloon.
        :return: Dynamic type of the balloon, if any.
        """

class DynamicTypeTracker(Protocol):
    """
    Efficiently tracks the dynamic type of a balloon.
    """

    def track(self, name: str, dynamic_type: type[B]) -> None:
        """
        Track the dynamic type of a balloon.

        :param name: Name of the balloon.
        :param dynamic_type: Dynamic type of the balloon.

        :raises ValueError: If a namespace conflict is detected.
        """


class EmptyDynamicTypeProvider(DynamicTypeProvider):
    """
    The dynamic type provider with no balloons.
    """

    def get(self, name: str, dynamic_type: type[B]) -> None:
        return None


class DynamicTypeManager(DynamicTypeProvider, DynamicTypeTracker):
    """
    Efficiently manages the dynamic types of balloons.
    """

    def __init__(
        self,
        namespace_types: set[type[Balloon]],
        base_provider: DynamicTypeProvider = EmptyDynamicTypeProvider(),
    ) -> None:
        """
        :param namespace_types: The balloon types that define a namespace.
        :param base_provider: The base provider of dynamic types.
        """
        self._namespace_types = namespace_types
        self._base_provider = base_provider

        self._name_to_dynamic_types: dict[str, set[type[Balloon]]] = defaultdict(set)

    def get(self, name: str, static_type: type[B]) -> type[B] | None:
        if all(not issubclass(static_type, t) for t in self._namespace_types):
            raise ValueError(f"Unsupported namespace type: {static_type}")

        dynamic_types = self._name_to_dynamic_types[name]

        candidate_dynamic_types = {t for t in dynamic_types if issubclass(t, static_type)}

        if len(candidate_dynamic_types) == 0:
            return self._base_provider.get(name, static_type)

        if len(candidate_dynamic_types) > 1:
            raise ValueError(f"Found multiple balloons with name: {name}")

        dynamic_type = candidate_dynamic_types.pop()
        return dynamic_type

    def track(self, name: str, dynamic_type: type[Balloon]) -> None:
        if self.get(name, dynamic_type) is dynamic_type:
            return

        relevant_namespace_types = {
            t for t in self._namespace_types if issubclass(dynamic_type, t)
        }
        for namespace_type in self._namespace_types:
            if not issubclass(dynamic_type, namespace_type):
                continue

            if (existing_dynamic_type := self.get(name, namespace_type)) is not None:
                raise ValueError(
                    "Found balloon with same name in different namespaces.\n"
                    f"Name: {name}\n"
                    f"Namespace type: {namespace_type}\n"
                    f"Existing type: {existing_dynamic_type}\n"
                    f"New type: {dynamic_type}"
                )

        self._name_to_dynamic_types[name].add(dynamic_type)


class BalloonProvider(Protocol[B]):  # type: ignore[misc]
    """
    Provides named balloons of a balloon type, including subtypes.
    """

    def get(self, name: str) -> B:
        """
        Provide the balloon with the given name, possibly inflating it from the JSON
        database if missing from memory.

        :param name: The balloon name.
        :return: The balloon.
        """


class BalloonTracker(Protocol[B]):  # type: ignore[misc]
    """
    Tracks named balloons of a balloon type, including subtypes.
    """

    def track(self, balloon: BN) -> None:
        """
        Track a balloon, possibly deflating it to the JSON database if missing from
        disk.

        :param balloon: The balloon to track.
        """


class FrozenBalloonist(BalloonProvider[B]):
    """
    Provides named balloons of a balloon type, including subtypes.
    """

    def __init__(
        self,
        type_: type[B],
        namespace_manager: DynamicTypeManager,
        balloon_providers: dict[type[Balloon], SpecializedBalloonProvider[NamedBalloon]],
    ) -> None:
        """
        :param type_: The type of the managed balloons.
        :param namespace_manager: The manager of the namespaces of balloons.
        :param balloon_providers: The specialized providers for each type of balloon.
        """
        self._type = type_
        self._namespace_manager = namespace_manager
        self._balloon_providers = balloon_providers

    def get(self, name: str) -> B:
        type_: type[Balloon] | None = self._namespace_manager.get(name, self._type)
        if type_ is None:
            raise ValueError(f"Could not find balloon with name: {name}")

        balloon_provider = self._balloon_providers[type_]
        return balloon_provider.get(name)

    def get_names(self) -> set[str]:
        names = set()
        for balloon_provider in self._balloon_providers.values():
            names.update(balloon_provider.get_names())
        return names


class Balloonist(BalloonProvider[B], BalloonTracker[B]):
    """
    Manages named balloons of a balloon type, including subtypes.
    """

    def __init__(
        self,
        type_: type[B],
        namespace_manager: DynamicTypeManager,
        balloon_managers: dict[type[Balloon], SpecializedBalloonManager[NamedBalloon]],
    ) -> None:
        """
        :param type_: The type of the managed balloons.
        :param name_to_type_manager: The manager to retrieve balloon types by name.
        :param balloon_managers: The specialized managers for each type of balloon.
        """
        self._type = type_
        self._namespace_manager = namespace_manager
        self._balloon_managers = balloon_managers

    def get(self, name: str) -> B:
        type_: type[Balloon] | None = self._namespace_manager.get(name, self._type)
        if type_ is None:
            raise ValueError(f"Could not find balloon with name: {name}")

        balloon_manager = self._balloon_managers[type_]  # type: ignore[index]
        return balloon_manager.get(name)  # type: ignore[return-value]

    def get_names(self) -> set[str]:
        names = set()
        for balloon_manager in self._balloon_managers.values():
            names.update(balloon_manager.get_names())
        return names

    def track(self, balloon: B) -> None:
        assert isinstance(balloon, NamedBalloon)
        named_type = type(balloon)
        type_ = named_type.Base

        tracked_type: type[Balloon] | None = self._namespace_manager.get(
            balloon.name, self._type
        )
        if tracked_type is not None:
            assert type_ is tracked_type

        balloon_manager = self._balloon_managers[type_]
        balloon_manager.track(balloon)
        self._namespace_manager.track(balloon.name, type_)


class FrozenBalloonDatabase:
    """
    A read-only database of balloons.
    """

    def __init__(
        self,
        namespace_types: set[type[Balloon]],
        balloon_providers: dict[
            type[Balloon], SpecializedBalloonProvider[NamedBalloon]
        ],
        namespace_manager: DynamicTypeManager,
    ) -> None:
        """
        :param namespace_types: The balloon types representing a namespace.
        :param ballon_providers: The specialized providers for each type of balloon.
        :param namespace_manager: The manager of the namespaces of balloons.
        """
        self._namespace_types = namespace_types
        self._balloon_providers = balloon_providers
        self._namespace_manager = namespace_manager

    def instantiate(self, type_: type[B]) -> FrozenBalloonist[B]:
        """
        Instantiate a balloon provider for a given type.

        :param type_: A balloon type.
        :return: The balloonist for the balloon type.
        """
        if all(not issubclass(type_, t) for t in self._namespace_types):
            raise ValueError(f"Unsupported balloonist balloon type: {type_}")

        balloon_providers: dict[
            type[Balloon], SpecializedBalloonManager[NamedBalloon]
        ] = {t: bs for t, bs in self._balloon_providers.items() if issubclass(t, type_)}

        return FrozenBalloonist(
            type_=type_,
            namespace_manager=self._namespace_manager,
            balloon_providers=balloon_providers,
        )

    # ---------------------------------------------------------------------------------

    def extend(
        self,
        database_path: Path,
        # TODO: Give the possibility to extend namespaces and schema types
        # namespace_types: set[type[Balloon]],
        # schema_types: set[type[Balloon]],
    ) -> FrozenBalloonDatabase:
        balloon_managers: dict[
            type[Balloon], SpecializedBalloonManager[NamedBalloon]
        ] = {}

        field_deflator = Deflator(
            trackers=balloon_managers,
        )
        field_inflator = Inflator(
            types_={t.__qualname__: t for t in types_},
            providers=balloon_managers,
        )
        for type_, balloon_provider in self._balloon_providers.items():
            jsons_path = database_path / type_.__qualname__
            jsons_path.mkdir(exist_ok=True)
            names = {p.stem for p in jsons_path.iterdir()}
            balloon_managers[type_] = SpecializedBalloonManager(
                type_=type_.Named,
                names=names,
                inflator=field_inflator,
                deflator=field_deflator,
                jsons_path=jsons_path,
                base_provider=balloon_provider,
            )

        namespace_manager = DynamicTypeManager(namespace_types=top_namespace_types)
        for type_, balloon_manager in balloon_managers.items():
            for name in balloon_manager.get_names():
                namespace_manager.track(name, type_)

        return FrozenBalloonDatabase(
            namespace_types=top_namespace_types,
            balloon_managers=balloon_managers,
            namespace_manager=namespace_manager,
        )

    def extend_as_writeable(self) -> BalloonDatabase:
        ...


class BalloonDatabase:
    """
    A database of balloons.
    """

    def __init__(
        self,
        namespace_types: set[type[Balloon]],
        balloon_managers: dict[type[Balloon], SpecializedBalloonManager[NamedBalloon]],
        namespace_manager: DynamicTypeManager,
    ) -> None:
        """
        :param namespace_types: The balloon types representing a namespace.
        :param balloon_managers: The specialized managers for each type of balloon.
        :param namespace_manager: The manager of the namespaces of balloons.
        """
        self._namespace_types = namespace_types
        self._balloon_managers = balloon_managers
        self._namespace_manager = namespace_manager

    def instantiate(self, type_: type[B]) -> Balloonist[B]:
        """
        Instantiate a balloonist for a balloon type

        :param type_: A balloon type.
        :return: The balloonist for the balloon type.
        """
        if all(not issubclass(type_, t) for t in self._namespace_types):
            raise ValueError(f"Unsupported balloonist balloon type: {type_}")

        balloon_managers: dict[
            type[Balloon], SpecializedBalloonManager[NamedBalloon]
        ] = {t: bs for t, bs in self._balloon_managers.items() if issubclass(t, type_)}

        return Balloonist(
            type_=type_,
            namespace_manager=self._namespace_manager,
            balloon_managers=balloon_managers,
        )

    @staticmethod
    def create(
        top_namespace_types: set[type[Balloon]],
        types_: set[type[Balloon]],
        json_database_path: Path,
    ) -> BalloonDatabase:
        """
        Create a factory for balloonists.

        :param top_namespace_types: The balloon types that define the top of their
            respective namespaces.
        :param types_: The balloon types.
        :param json_database_path: The path to the JSON database.
        :return: The factory for balloonists.
        """
        balloon_managers: dict[
            type[Balloon], SpecializedBalloonManager[NamedBalloon]
        ] = {}

        field_deflator = Deflator(
            trackers=balloon_managers,
        )
        field_inflator = Inflator(
            types_={t.__qualname__: t for t in types_},
            providers=balloon_managers,
        )
        for type_ in types_:
            if not any(issubclass(type_, t) for t in top_namespace_types):
                continue
            jsons_path = json_database_path / type_.__qualname__
            jsons_path.mkdir(exist_ok=True)
            names = {p.stem for p in jsons_path.iterdir()}
            balloon_managers[type_] = SpecializedBalloonManager(
                type_=type_.Named,
                names=names,
                inflator=field_inflator,
                deflator=field_deflator,
                jsons_path=jsons_path,
            )

        namespace_manager = DynamicTypeManager(namespace_types=top_namespace_types)
        for type_, balloon_manager in balloon_managers.items():
            for name in balloon_manager.get_names():
                namespace_manager.track(name, type_)

        return BalloonDatabase(
            namespace_types=top_namespace_types,
            balloon_managers=balloon_managers,
            namespace_manager=namespace_manager,
        )
