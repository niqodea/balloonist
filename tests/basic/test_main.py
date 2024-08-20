from __future__ import annotations

from pathlib import Path

from balloons import BalloonistFactory

from tests.basic.schema import Animal, Cat, Dog, Owner
from tests.basic.objects import (
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

JSON_DATABASE_PATH = Path(__file__).parent / "database"


def get_balloonist_factory(json_database_path: Path) -> BalloonistFactory:
    return BalloonistFactory.create(
        top_namespace_types={Animal, Owner},
        types_={Animal, Animal.Size, Cat, Dog, Owner},
        json_database_path=json_database_path,
    )


def test_inflation(tmp_path: Path) -> None:
    balloonist_factory = get_balloonist_factory(JSON_DATABASE_PATH)
    animal_balloonist = balloonist_factory.instantiate(Animal)
    owner_balloonist = balloonist_factory.instantiate(Owner)

    # Cats
    abigail = animal_balloonist.get(ABIGAIL.as_named().name)
    benjamin = animal_balloonist.get(BENJAMIN.as_named().name)
    charlotte = animal_balloonist.get(CHARLOTTE.as_named().name)
    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE
    # Dogs
    alex = animal_balloonist.get(ALEX.as_named().name)
    bella = animal_balloonist.get(BELLA.as_named().name)
    cody = animal_balloonist.get(CODY.as_named().name)
    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY
    # Owners
    alice = owner_balloonist.get(ALICE.as_named().name)
    bob = owner_balloonist.get(BOB.as_named().name)
    carol = owner_balloonist.get(CAROL.as_named().name)
    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL


def test_consistency(tmp_path: Path) -> None:
    balloonist_factory = get_balloonist_factory(tmp_path)
    animal_balloonist = balloonist_factory.instantiate(Animal)
    owner_balloonist = balloonist_factory.instantiate(Owner)

    # Cats
    animal_balloonist.track(ABIGAIL)
    animal_balloonist.track(BENJAMIN)
    animal_balloonist.track(CHARLOTTE)
    # Dogs
    animal_balloonist.track(ALEX)
    animal_balloonist.track(BELLA)
    animal_balloonist.track(CODY)
    # Owners
    owner_balloonist.track(ALICE)
    owner_balloonist.track(BOB)
    owner_balloonist.track(CAROL)

    # Simulate a new Python session by creating the objects again

    other_balloonist_factory = get_balloonist_factory(tmp_path)
    other_animal_balloonist = other_balloonist_factory.instantiate(Animal)
    other_owner_balloonist = other_balloonist_factory.instantiate(Owner)

    # Cats
    abigail = other_animal_balloonist.get(ABIGAIL.as_named().name)
    benjamin = other_animal_balloonist.get(BENJAMIN.as_named().name)
    charlotte = other_animal_balloonist.get(CHARLOTTE.as_named().name)
    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE
    # Dogs
    alex = other_animal_balloonist.get(ALEX.as_named().name)
    bella = other_animal_balloonist.get(BELLA.as_named().name)
    cody = other_animal_balloonist.get(CODY.as_named().name)
    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY
    # Owners
    alice = other_owner_balloonist.get(ALICE.as_named().name)
    bob = other_owner_balloonist.get(BOB.as_named().name)
    carol = other_owner_balloonist.get(CAROL.as_named().name)
    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL
