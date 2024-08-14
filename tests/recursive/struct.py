from __future__ import annotations

from tests.recursive.schema import CompositeFood, SimpleFood

APPLE = SimpleFood(name="apple", calories=10)

BANANA = SimpleFood(name="banana", calories=20)

CARROT = SimpleFood(name="carrot", calories=5)

DATE = SimpleFood(name="date", calories=30)

FRUIT_SALAD = CompositeFood(
    name="fruit-salad",
    ingredients=frozenset({APPLE, BANANA}),
)

VEGETABLE_SALAD = CompositeFood(
    name="vegetable-salad",
    ingredients=frozenset({CARROT, DATE}),
)

FRUIT_AND_VEGETABLE_SALAD = CompositeFood(
    name="fruit-and-vegetable-salad",
    ingredients=frozenset({FRUIT_SALAD, VEGETABLE_SALAD}),
)
