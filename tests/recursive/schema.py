from __future__ import annotations

from dataclasses import dataclass

from balloons import Balloon, balloon


@balloon
class Food(Balloon): ...


@balloon
class SimpleFood(Food):
    calories: int


@balloon
class CompositeFood(Food):
    ingredients: set[Food]
