from __future__ import annotations

from dataclasses import dataclass

from balloons import NamedBalloon


@dataclass(frozen=True)
class Food(NamedBalloon): ...


@dataclass(frozen=True)
class SimpleFood(Food):
    calories: int


@dataclass(frozen=True)
class CompositeFood(Food):
    ingredients: set[Food]
