from __future__ import annotations

from pathlib import Path

from balloonist import BalloonistProvider

from tests.recursive.schema import CompositeFood, Food, Named, SimpleFood
from tests.recursive.struct import (
    APPLE,
    BANANA,
    CARROT,
    DATE,
    FRUIT_AND_VEGETABLE_SALAD,
    FRUIT_SALAD,
    VEGETABLE_SALAD,
)

STRUCT_JSONS_PATH = Path(__file__).parent / "struct"


def get_balloonist_provider(jsons_root: Path) -> BalloonistProvider:
    return BalloonistProvider.create(
        base_types={Food, SimpleFood, CompositeFood},
        named_types={
            SimpleFood: Named.SimpleFood,
            CompositeFood: Named.CompositeFood,
        },
        jsons_root=jsons_root,
    )


def test_inflation(tmp_path: Path) -> None:
    balloonist_provider = get_balloonist_provider(STRUCT_JSONS_PATH)

    simple_food_balloonist = balloonist_provider.get(Named.SimpleFood)
    apple = simple_food_balloonist.get(APPLE.name)
    banana = simple_food_balloonist.get(BANANA.name)
    carrot = simple_food_balloonist.get(CARROT.name)
    date = simple_food_balloonist.get(DATE.name)

    assert apple == APPLE
    assert banana == BANANA
    assert carrot == CARROT
    assert date == DATE

    composite_food_balloonist = balloonist_provider.get(Named.CompositeFood)
    fruit_salad = composite_food_balloonist.get(FRUIT_SALAD.name)
    vegetable_salad = composite_food_balloonist.get(VEGETABLE_SALAD.name)
    fruit_and_vegetable_salad = composite_food_balloonist.get(
        FRUIT_AND_VEGETABLE_SALAD.name
    )

    assert fruit_salad == FRUIT_SALAD
    assert vegetable_salad == VEGETABLE_SALAD
    assert fruit_and_vegetable_salad == FRUIT_AND_VEGETABLE_SALAD


def test_consistency(tmp_path: Path) -> None:
    balloonist_provider = get_balloonist_provider(tmp_path)

    simple_food_balloonist = balloonist_provider.get(Named.SimpleFood)
    simple_food_balloonist.store(APPLE)
    simple_food_balloonist.store(BANANA)
    simple_food_balloonist.store(CARROT)
    simple_food_balloonist.store(DATE)

    composite_food_balloonist = balloonist_provider.get(Named.CompositeFood)
    composite_food_balloonist.store(FRUIT_SALAD)
    composite_food_balloonist.store(VEGETABLE_SALAD)
    composite_food_balloonist.store(FRUIT_AND_VEGETABLE_SALAD)

    other_balloonist_provider = get_balloonist_provider(tmp_path)

    other_simple_food_balloonist = other_balloonist_provider.get(Named.SimpleFood)

    apple = other_simple_food_balloonist.get(APPLE.name)
    banana = other_simple_food_balloonist.get(BANANA.name)
    carrot = other_simple_food_balloonist.get(CARROT.name)
    date = other_simple_food_balloonist.get(DATE.name)

    assert apple == APPLE
    assert banana == BANANA
    assert carrot == CARROT
    assert date == DATE

    other_composite_food_balloonist = other_balloonist_provider.get(Named.CompositeFood)

    fruit_salad = other_composite_food_balloonist.get(FRUIT_SALAD.name)
    vegetable_salad = other_composite_food_balloonist.get(VEGETABLE_SALAD.name)
    fruit_and_vegetable_salad = other_composite_food_balloonist.get(
        FRUIT_AND_VEGETABLE_SALAD.name
    )

    assert fruit_salad == FRUIT_SALAD
    assert vegetable_salad == VEGETABLE_SALAD
    assert fruit_and_vegetable_salad == FRUIT_AND_VEGETABLE_SALAD
