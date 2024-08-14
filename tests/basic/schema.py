from __future__ import annotations

from dataclasses import dataclass

from balloons import AnonBalloon, FrozenDict, NamedBalloon


@dataclass(frozen=True)
class Animal(NamedBalloon):
    size: Size

    @dataclass(frozen=True)
    class Size(AnonBalloon):
        height: int
        weight: int


@dataclass(frozen=True)
class Cat(Animal):
    purr_type: str | None


@dataclass(frozen=True)
class Dog(Animal):
    obedience: float


@dataclass(frozen=True)
class Owner(NamedBalloon):
    pet_nicknames: FrozenDict[Animal, str]
