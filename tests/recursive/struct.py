from __future__ import annotations

from tests.recursive.schema import Named

APPLE = Named.SimpleFood(name="apple", calories=10)

BANANA = Named.SimpleFood(name="banana", calories=20)

CARROT = Named.SimpleFood(name="carrot", calories=5)

DATE = Named.SimpleFood(name="date", calories=30)

FRUIT_SALAD = Named.CompositeFood(
    name="fruit-salad",
    ingredients=frozenset({APPLE, BANANA}),
)

VEGETABLE_SALAD = Named.CompositeFood(
    name="vegetable-salad",
    ingredients=frozenset({CARROT, DATE}),
)

FRUIT_AND_VEGETABLE_SALAD = Named.CompositeFood(
    name="fruit-and-vegetable-salad",
    ingredients=frozenset({FRUIT_SALAD, VEGETABLE_SALAD}),
)
