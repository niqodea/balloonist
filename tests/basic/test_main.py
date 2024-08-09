from __future__ import annotations

from pathlib import Path

from balloonist import BalloonistProvider

from tests.basic.schema import Animal, Cat, Dog, Named, Owner
from tests.basic.struct import (
    ABIGAIL,
    ALEX,
    ALICE,
    BELLA,
    BENJAMIN,
    BOB,
    CAROL,
    CHARLOTTE,
    CODY,
)

STRUCT_JSONS_PATH = Path(__file__).parent / "struct"


def get_balloonist_provider(jsons_root: Path) -> BalloonistProvider:
    return BalloonistProvider.create(
        base_types={Animal, Animal.Size, Cat, Dog, Owner},
        named_types={
            Cat: Named.Cat,
            Dog: Named.Dog,
            Owner: Named.Owner,
        },
        jsons_root=jsons_root,
    )


def test_inflation(tmp_path: Path) -> None:
    balloonist_provider = get_balloonist_provider(STRUCT_JSONS_PATH)

    cat_balloonist = balloonist_provider.get(Named.Cat)
    abigail = cat_balloonist.get(ABIGAIL.name)
    benjamin = cat_balloonist.get(BENJAMIN.name)
    charlotte = cat_balloonist.get(CHARLOTTE.name)

    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE

    dog_balloonist = balloonist_provider.get(Named.Dog)
    alex = dog_balloonist.get(ALEX.name)
    bella = dog_balloonist.get(BELLA.name)
    cody = dog_balloonist.get(CODY.name)

    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY

    owner_balloonist = balloonist_provider.get(Named.Owner)
    alice = owner_balloonist.get(ALICE.name)
    bob = owner_balloonist.get(BOB.name)
    carol = owner_balloonist.get(CAROL.name)

    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL


def test_consistency(tmp_path: Path) -> None:
    balloonist_provider = get_balloonist_provider(tmp_path)

    cat_balloonist = balloonist_provider.get(Named.Cat)
    cat_balloonist.store(ABIGAIL)
    cat_balloonist.store(BENJAMIN)
    cat_balloonist.store(CHARLOTTE)

    dog_balloonist = balloonist_provider.get(Named.Dog)
    dog_balloonist.store(ALEX)
    dog_balloonist.store(BELLA)
    dog_balloonist.store(CODY)

    owner_balloonist = balloonist_provider.get(Named.Owner)
    owner_balloonist.store(ALICE)
    owner_balloonist.store(BOB)
    owner_balloonist.store(CAROL)

    other_balloonist_provider = get_balloonist_provider(tmp_path)

    other_cat_balloonist = other_balloonist_provider.get(Named.Cat)

    abigail = other_cat_balloonist.get(ABIGAIL.name)
    benjamin = other_cat_balloonist.get(BENJAMIN.name)
    charlotte = other_cat_balloonist.get(CHARLOTTE.name)

    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE

    other_dog_balloonist = other_balloonist_provider.get(Named.Dog)

    alex = other_dog_balloonist.get(ALEX.name)
    bella = other_dog_balloonist.get(BELLA.name)
    cody = other_dog_balloonist.get(CODY.name)

    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY

    other_owner_balloonist = other_balloonist_provider.get(Named.Owner)

    alice = other_owner_balloonist.get(ALICE.name)
    bob = other_owner_balloonist.get(BOB.name)
    carol = other_owner_balloonist.get(CAROL.name)

    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL
