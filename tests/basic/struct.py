from balloonist import FrozenDict

from tests.basic.schema import Animal, Named

ABIGAIL = Named.Cat(
    name="abigail",
    size=Animal.Size(height=10, weight=5),
    purr_type="loud",
)

BENJAMIN = Named.Cat(
    name="benjamin",
    size=Animal.Size(height=15, weight=8),
    purr_type="soft",
)

CHARLOTTE = Named.Cat(
    name="charlotte",
    size=Animal.Size(height=12, weight=7),
    purr_type=None,
)


ALEX = Named.Dog(
    name="alex",
    size=Animal.Size(height=20, weight=10),
    obedience=0.9,
)

BELLA = Named.Dog(
    name="bella",
    size=Animal.Size(height=25, weight=15),
    obedience=0.7,
)

CODY = Named.Dog(
    name="cody",
    size=Animal.Size(height=22, weight=12),
    obedience=0.8,
)


ALICE = Named.Owner(
    name="alice",
    pet_nicknames=FrozenDict({ABIGAIL: "abby", ALEX: "ale"}),
)

BOB = Named.Owner(
    name="bob",
    pet_nicknames=FrozenDict({BENJAMIN: "ben", BELLA: "bel"}),
)

CAROL = Named.Owner(
    name="carol",
    pet_nicknames=FrozenDict({CHARLOTTE: "charlie", CODY: "cod"}),
)
