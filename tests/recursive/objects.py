from __future__ import annotations

from tests.recursive.schema import CompositeFood, SimpleFood

APPLE = SimpleFood(calories=10).to_named("apple")

BANANA = SimpleFood(calories=20).to_named("banana")

CARROT = SimpleFood(calories=5).to_named("carrot")

DATE = SimpleFood(calories=30).to_named("date")

FRUIT_SALAD = CompositeFood(
    ingredients={APPLE, BANANA},
).to_named("fruit-salad")

VEGETABLE_SALAD = CompositeFood(
    ingredients={CARROT, DATE},
).to_named("vegetable-salad")

FRUIT_AND_VEGETABLE_SALAD = CompositeFood(
    ingredients={FRUIT_SALAD, VEGETABLE_SALAD},
).to_named("fruit-and-vegetable-salad")
