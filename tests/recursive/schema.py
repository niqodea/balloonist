from __future__ import annotations

from dataclasses import dataclass

from balloonist import NamedStruct, Struct


@dataclass(frozen=True)
class Food(Struct): ...


@dataclass(frozen=True)
class SimpleFood(Food):
    calories: int


@dataclass(frozen=True)
class CompositeFood(Food):
    ingredients: frozenset[Food]


class Named:
    @dataclass(frozen=True)
    class SimpleFood(SimpleFood, NamedStruct): ...  # type: ignore[misc]

    @dataclass(frozen=True)
    class CompositeFood(CompositeFood, NamedStruct): ...  # type: ignore[misc]
