from __future__ import annotations

from dataclasses import dataclass

from balloonist import FrozenDict, NamedStruct, Struct


@dataclass(frozen=True)
class Animal(Struct):
    size: Size

    @dataclass(frozen=True)
    class Size(Struct):
        height: int
        weight: int


@dataclass(frozen=True)
class Cat(Animal):
    purr_type: str | None


@dataclass(frozen=True)
class Dog(Animal):
    obedience: float


@dataclass(frozen=True)
class Owner(Struct):
    pet_nicknames: FrozenDict[Animal, str]


class Named:
    @dataclass(frozen=True)
    class Cat(Cat, NamedStruct): ...  # type: ignore[misc]

    @dataclass(frozen=True)
    class Dog(Dog, NamedStruct): ...  # type: ignore[misc]

    @dataclass(frozen=True)
    class Owner(Owner, NamedStruct): ...  # type: ignore[misc]
