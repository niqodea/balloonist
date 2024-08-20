from enum import Enum

from tests.basic.schema import Animal, Cat, Dog, Owner


# Cats
ABIGAIL = Cat(
    size=Animal.Size(height=10, weight=5),
    purr_type="loud",
).to_named("abigail")
BENJAMIN = Cat(
    size=Animal.Size(height=15, weight=8),
    purr_type="soft",
).to_named("benjamin")
CHARLOTTE = Cat(
    size=Animal.Size(height=12, weight=7),
    purr_type=None,
).to_named("charlotte")

# Dogs
ALEX = Dog(
    size=Animal.Size(height=20, weight=10),
    obedience=0.9,
).to_named("alex")
BELLA = Dog(
    size=Animal.Size(height=25, weight=15),
    obedience=0.7,
).to_named("bella")
CODY = Dog(
    size=Animal.Size(height=22, weight=12),
    obedience=0.8,
).to_named("cody")

# Owners
ALICE = Owner(
    pet_nicknames={ABIGAIL: "abby", ALEX: "ale"},
).to_named("alice")
BOB = Owner(
    pet_nicknames={BENJAMIN: "ben", BELLA: "bel"},
).to_named("bob")
CAROL = Owner(
    pet_nicknames={CHARLOTTE: "charlie", CODY: "cod"},
).to_named("carol")
