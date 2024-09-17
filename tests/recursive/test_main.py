from __future__ import annotations

from pathlib import Path

from balloons import ClosedBalloonWorld
from tests.recursive.objects import (
    APPLE,
    BANANA,
    CARROT,
    DATE,
    FRUIT_AND_VEGETABLE_SALAD,
    FRUIT_SALAD,
    VEGETABLE_SALAD,
)
from tests.recursive.schema import CompositeFood, Food, SimpleFood

DATABASE_PATH = Path(__file__).parent / "database"

BASE_WORLD = ClosedBalloonWorld.create(
    namespace_types={Food},
    types_={Food, SimpleFood, CompositeFood},
)


def test_inflation(tmp_path: Path) -> None:
    world = BASE_WORLD.populate(DATABASE_PATH)
    food_provider = world.get_provider(Food)

    # Simple
    apple = food_provider.get(APPLE.as_named().name)
    banana = food_provider.get(BANANA.as_named().name)
    carrot = food_provider.get(CARROT.as_named().name)
    date = food_provider.get(DATE.as_named().name)
    assert apple == APPLE
    assert banana == BANANA
    assert carrot == CARROT
    assert date == DATE
    # Composite
    fruit_salad = food_provider.get(FRUIT_SALAD.as_named().name)
    vegetable_salad = food_provider.get(VEGETABLE_SALAD.as_named().name)
    fruit_and_vegetable_salad = food_provider.get(
        FRUIT_AND_VEGETABLE_SALAD.as_named().name
    )
    assert fruit_salad == FRUIT_SALAD
    assert vegetable_salad == VEGETABLE_SALAD
    assert fruit_and_vegetable_salad == FRUIT_AND_VEGETABLE_SALAD


def test_consistency(tmp_path: Path) -> None:
    world = BASE_WORLD.to_open(tmp_path)
    food_tracker = world.get_tracker(Food)

    # Simple
    food_tracker.track(APPLE)
    food_tracker.track(BANANA)
    food_tracker.track(CARROT)
    food_tracker.track(DATE)
    # Composite
    food_tracker.track(FRUIT_SALAD)
    food_tracker.track(VEGETABLE_SALAD)
    food_tracker.track(FRUIT_AND_VEGETABLE_SALAD)

    # Simulate a new Python session by creating the objects again

    other_world = BASE_WORLD.populate(DATABASE_PATH)
    food_provider = other_world.get_provider(Food)

    # Simple
    apple = food_provider.get(APPLE.as_named().name)
    banana = food_provider.get(BANANA.as_named().name)
    carrot = food_provider.get(CARROT.as_named().name)
    date = food_provider.get(DATE.as_named().name)
    assert apple == APPLE
    assert banana == BANANA
    assert carrot == CARROT
    assert date == DATE
    # Composite
    fruit_salad = food_provider.get(FRUIT_SALAD.as_named().name)
    vegetable_salad = food_provider.get(VEGETABLE_SALAD.as_named().name)
    fruit_and_vegetable_salad = food_provider.get(
        FRUIT_AND_VEGETABLE_SALAD.as_named().name
    )
    assert fruit_salad == FRUIT_SALAD
    assert vegetable_salad == VEGETABLE_SALAD
    assert fruit_and_vegetable_salad == FRUIT_AND_VEGETABLE_SALAD
