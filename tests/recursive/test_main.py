from __future__ import annotations

from pathlib import Path

from balloons import BalloonistFactory

from tests.recursive.schema import CompositeFood, Food, SimpleFood
from tests.recursive.struct import (
    APPLE,
    BANANA,
    CARROT,
    DATE,
    FRUIT_AND_VEGETABLE_SALAD,
    FRUIT_SALAD,
    VEGETABLE_SALAD,
)

JSON_DATABASE_PATH = Path(__file__).parent / "database"


def get_balloonist_factory(json_database_path: Path) -> BalloonistFactory:
    return BalloonistFactory.create(
        top_namespace_types={Food},
        named_concrete_types={SimpleFood, CompositeFood},
        anon_concrete_types=set(),
        json_database_path=json_database_path,
    )


def test_inflation(tmp_path: Path) -> None:
    balloonist_factory = get_balloonist_factory(JSON_DATABASE_PATH)

    balloonist = balloonist_factory.instantiate(Food)

    # Simple
    apple = balloonist.get(APPLE.name)
    banana = balloonist.get(BANANA.name)
    carrot = balloonist.get(CARROT.name)
    date = balloonist.get(DATE.name)
    assert apple == APPLE
    assert banana == BANANA
    assert carrot == CARROT
    assert date == DATE
    # Composite
    fruit_salad = balloonist.get(FRUIT_SALAD.name)
    vegetable_salad = balloonist.get(VEGETABLE_SALAD.name)
    fruit_and_vegetable_salad = balloonist.get(FRUIT_AND_VEGETABLE_SALAD.name)
    assert fruit_salad == FRUIT_SALAD
    assert vegetable_salad == VEGETABLE_SALAD
    assert fruit_and_vegetable_salad == FRUIT_AND_VEGETABLE_SALAD


def test_consistency(tmp_path: Path) -> None:
    balloonist_factory = get_balloonist_factory(tmp_path)
    balloonist = balloonist_factory.instantiate(Food)

    # Simple
    balloonist.track(APPLE)
    balloonist.track(BANANA)
    balloonist.track(CARROT)
    balloonist.track(DATE)
    # Composite
    balloonist.track(FRUIT_SALAD)
    balloonist.track(VEGETABLE_SALAD)
    balloonist.track(FRUIT_AND_VEGETABLE_SALAD)

    # Simulate a new Python session by creating the objects again

    other_balloonist_factory = get_balloonist_factory(tmp_path)
    other_balloonist = other_balloonist_factory.instantiate(Food)

    # Simple
    apple = other_balloonist.get(APPLE.name)
    banana = other_balloonist.get(BANANA.name)
    carrot = other_balloonist.get(CARROT.name)
    date = other_balloonist.get(DATE.name)
    assert apple == APPLE
    assert banana == BANANA
    assert carrot == CARROT
    assert date == DATE
    # Composite
    fruit_salad = other_balloonist.get(FRUIT_SALAD.name)
    vegetable_salad = other_balloonist.get(VEGETABLE_SALAD.name)
    fruit_and_vegetable_salad = other_balloonist.get(FRUIT_AND_VEGETABLE_SALAD.name)
    assert fruit_salad == FRUIT_SALAD
    assert vegetable_salad == VEGETABLE_SALAD
    assert fruit_and_vegetable_salad == FRUIT_AND_VEGETABLE_SALAD
