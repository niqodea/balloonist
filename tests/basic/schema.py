from __future__ import annotations

from dataclasses import dataclass

from balloons import AnonBalloon, NamedBalloon


@dataclass(frozen=True, eq=False)
class Animal(NamedBalloon):
    size: Size

    @dataclass(frozen=True)
    class Size(AnonBalloon):
        height: int
        weight: int


@dataclass(frozen=True, eq=False)
class Cat(Animal):
    purr_type: str | None


@dataclass(frozen=True, eq=False)
class Dog(Animal):
    obedience: float


@dataclass(frozen=True, eq=False)
class Owner(NamedBalloon):
    pet_nicknames: dict[Animal, str]
