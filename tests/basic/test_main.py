from __future__ import annotations

from pathlib import Path

from balloons import BalloonistFactory

from tests.basic.schema import Animal, Cat, Dog, NamedBalloon, Owner
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

JSON_DATABASE_PATH = Path(__file__).parent / "database"


def get_balloonist_factory(json_database_path: Path) -> BalloonistFactory:
    return BalloonistFactory.create(
        top_namespace_types={NamedBalloon},
        named_concrete_types={Cat, Dog, Owner},
        anon_concrete_types={Animal.Size},
        json_database_path=json_database_path,
    )


def test_inflation(tmp_path: Path) -> None:
    balloonist_factory = get_balloonist_factory(JSON_DATABASE_PATH)
    balloonist = balloonist_factory.instantiate(NamedBalloon)

    # Cats
    abigail = balloonist.get(ABIGAIL.name)
    benjamin = balloonist.get(BENJAMIN.name)
    charlotte = balloonist.get(CHARLOTTE.name)
    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE
    # Dogs
    alex = balloonist.get(ALEX.name)
    bella = balloonist.get(BELLA.name)
    cody = balloonist.get(CODY.name)
    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY
    # Owners
    alice = balloonist.get(ALICE.name)
    bob = balloonist.get(BOB.name)
    carol = balloonist.get(CAROL.name)
    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL


def test_consistency(tmp_path: Path) -> None:
    balloonist_factory = get_balloonist_factory(tmp_path)

    balloonist = balloonist_factory.instantiate(NamedBalloon)

    # Cats
    balloonist.track(ABIGAIL)
    balloonist.track(BENJAMIN)
    balloonist.track(CHARLOTTE)
    # Dogs
    balloonist.track(ALEX)
    balloonist.track(BELLA)
    balloonist.track(CODY)
    # Owners
    balloonist.track(ALICE)
    balloonist.track(BOB)
    balloonist.track(CAROL)

    # Simulate a new Python session by creating the objects again

    other_balloonist_factory = get_balloonist_factory(tmp_path)
    other_balloonist = other_balloonist_factory.instantiate(NamedBalloon)

    # Cats
    abigail = other_balloonist.get(ABIGAIL.name)
    benjamin = other_balloonist.get(BENJAMIN.name)
    charlotte = other_balloonist.get(CHARLOTTE.name)
    assert abigail == ABIGAIL
    assert benjamin == BENJAMIN
    assert charlotte == CHARLOTTE
    # Dogs
    alex = other_balloonist.get(ALEX.name)
    bella = other_balloonist.get(BELLA.name)
    cody = other_balloonist.get(CODY.name)
    assert alex == ALEX
    assert bella == BELLA
    assert cody == CODY
    # Owners
    alice = other_balloonist.get(ALICE.name)
    bob = other_balloonist.get(BOB.name)
    carol = other_balloonist.get(CAROL.name)
    assert alice == ALICE
    assert bob == BOB
    assert carol == CAROL
