from __future__ import annotations

from pathlib import Path

from balloons import ClosedBalloonWorld
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
from tests.basic.schema import Animal, Cat, Dog, Owner

DATABASE_PATH = Path(__file__).parent / "database"

BASE_WORLD = ClosedBalloonWorld.create(
    namespace_types={Animal, Owner},
    types_={Animal, Animal.Size, Cat, Dog, Owner},
)


def test_inflation(tmp_path: Path) -> None:
    world = BASE_WORLD.populate(DATABASE_PATH)
    animal_provider = world.get_provider(Animal)
    owner_provider = world.get_provider(Owner)

    # Cats
    abigail = animal_provider.get(ABIGAIL.as_named().name)
    benjamin = animal_provider.get(BENJAMIN.as_named().name)
    charlotte = animal_provider.get(CHARLOTTE.as_named().name)
    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE
    # Dogs
    alex = animal_provider.get(ALEX.as_named().name)
    bella = animal_provider.get(BELLA.as_named().name)
    cody = animal_provider.get(CODY.as_named().name)
    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY
    # Owners
    alice = owner_provider.get(ALICE.as_named().name)
    bob = owner_provider.get(BOB.as_named().name)
    carol = owner_provider.get(CAROL.as_named().name)
    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL


def test_consistency(tmp_path: Path) -> None:
    world = BASE_WORLD.to_open(tmp_path)
    animal_tracker = world.get_tracker(Animal)
    owner_tracker = world.get_tracker(Owner)

    # Cats
    animal_tracker.track(ABIGAIL)
    animal_tracker.track(BENJAMIN)
    animal_tracker.track(CHARLOTTE)
    # Dogs
    animal_tracker.track(ALEX)
    animal_tracker.track(BELLA)
    animal_tracker.track(CODY)
    # Owners
    owner_tracker.track(ALICE)
    owner_tracker.track(BOB)
    owner_tracker.track(CAROL)

    # Simulate a new Python session by creating the objects again

    other_world = BASE_WORLD.populate(tmp_path)
    animal_provider = other_world.get_provider(Animal)
    owner_provider = other_world.get_provider(Owner)

    # Cats
    abigail = animal_provider.get(ABIGAIL.as_named().name)
    benjamin = animal_provider.get(BENJAMIN.as_named().name)
    charlotte = animal_provider.get(CHARLOTTE.as_named().name)
    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE
    # Dogs
    alex = animal_provider.get(ALEX.as_named().name)
    bella = animal_provider.get(BELLA.as_named().name)
    cody = animal_provider.get(CODY.as_named().name)
    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY
    # Owners
    alice = owner_provider.get(ALICE.as_named().name)
    bob = owner_provider.get(BOB.as_named().name)
    carol = owner_provider.get(CAROL.as_named().name)
    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL
