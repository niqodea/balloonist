from balloons import FrozenDict

from tests.basic.schema import Animal, Cat, Dog, Owner

ABIGAIL = Cat(
    name="abigail",
    size=Animal.Size(height=10, weight=5),
    purr_type="loud",
)

BENJAMIN = Cat(
    name="benjamin",
    size=Animal.Size(height=15, weight=8),
    purr_type="soft",
)

CHARLOTTE = Cat(
    name="charlotte",
    size=Animal.Size(height=12, weight=7),
    purr_type=None,
)


ALEX = Dog(
    name="alex",
    size=Animal.Size(height=20, weight=10),
    obedience=0.9,
)

BELLA = Dog(
    name="bella",
    size=Animal.Size(height=25, weight=15),
    obedience=0.7,
)

CODY = Dog(
    name="cody",
    size=Animal.Size(height=22, weight=12),
    obedience=0.8,
)


ALICE = Owner(
    name="alice",
    pet_nicknames=FrozenDict({ABIGAIL: "abby", ALEX: "ale"}),
)

BOB = Owner(
    name="bob",
    pet_nicknames=FrozenDict({BENJAMIN: "ben", BELLA: "bel"}),
)

CAROL = Owner(
    name="carol",
    pet_nicknames=FrozenDict({CHARLOTTE: "charlie", CODY: "cod"}),
)
