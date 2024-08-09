# balloonist

A Python library to deflate dataclasses to JSON files and inflate them back.

## Usage

Extend the `Struct` base class to define a schema that can be handled by balloonist.

For example:

```py
from dataclasses import dataclass
from balloonist import FrozenDict, Struct

@dataclass(frozen=True)
class Animal(Struct):
    size: Size

    @dataclass(frozen=True)
    class Size(Struct):
        height: int
        weight: int

@dataclass(frozen=True)
class Cat(Animal):
    purr_type: str | None

@dataclass(frozen=True)
class Dog(Animal):
    obedience: float

@dataclass(frozen=True)
class Owner(Struct):
    pet_nicknames: FrozenDict[Animal, str]
```

After defining the schema, you can further extend some classes with the `NamedStruct` marker class to create named struct instances, which can be stored in, or retrieved from, a database of JSON files.

For example:

```py
from balloonist import NamedStruct

class Named:
    @dataclass(frozen=True)
    class Cat(Cat, NamedStruct): ...

    @dataclass(frozen=True)
    class Dog(Dog, NamedStruct): ...

    @dataclass(frozen=True)
    class Owner(Owner, NamedStruct): ...


ABIGAIL = Named.Cat(
    name="abigail",
    size=Animal.Size(height=10, weight=5),
    purr_type="loud",
)

ALEX = Named.Dog(
    name="alex",
    size=Animal.Size(height=20, weight=10),
    obedience=0.9,
)

ALICE = Named.Owner(
    name="alice",
    pet_nicknames=FrozenDict({ABIGAIL: "abby", ALEX: "ale"}),
)

```

You will need to instantiate a `Balloonist` to store your named structs at runtime:

```py
from pathlib import Path
from balloonist import BalloonistProvider

balloonist_provider = BalloonistProvider.create(
    # Inform balloonist of all possible struct types
    base_types={Animal, Animal.Size, Cat, Dog, Owner},
    # Inform balloonist of base-to-named struct type correspondence
    named_types={
        Cat: Named.Cat,
        Dog: Named.Dog,
        Owner: Named.Owner,
    },
    # Where to store the JSON files
    jsons_root=Path("/path/to/jsons"),
)

cat_balloonist = balloonist_provider.get(Named.Cat)
dog_balloonist = balloonist_provider.get(Named.Dog)
owner_balloonist = balloonist_provider.get(Named.Owner)

# Deflate structs to a JSON file
cat_balloonist.store(ABIGAIL)
dog_balloonist.store(ALEX)
owner_balloonist.store(ALICE)
```

After storing named structs, you can retrieve them in another Python session:


```py
# In another Python session...
ABIGAIL = cat_balloonist.get("abigail")
ALEX = dog_balloonist.get("alex")
ALICE = owner_balloonist.get("alice")
```

## Database

### File Structure

Starting from the root directory, we have a flat list of subdirectories, one for each named struct type.
Each subdirectory contains a JSON file for each instance of that struct type, named after the instance name.

For example, this is a possible database structure:

```
struct/
│
├─── Cat/
│    ├─── abigail.json
│    ├─── benjamin.json
│    └─── charlotte.json
│
├─── Dog/
│    ├─── alex.json
│    ├─── bella.json
│    └─── cody.json
│
└─── Owner/
     ├─── alice.json
     ├─── bob.json
     └─── carol.json
```

*Note*: Since named struct type names are generally a trivial extension of the base type (e.g. `Cat` -> `Named.Cat`), we name the subdirectories after the base types instead.

### JSON Structure

Each JSON file contains the deflated fields of the instance as a dictionary mapping field name to value.

During deflation, references to other named instances are resolved by keeping track of their type and name.
This provides benefits such as easy data reuse and enhanced data integrity.

Generally, we convert structs to JSON dictionaries as they are the most flexible construct for this purpose.
However, when using a struct as a dictionary key, we need to convert them to strings to conform to the JSON standard. 
While this conversion is supported for both named and anonymous instances, the former behave better in this regard, as there is only the need to store type and name of the instance.
Having a complex anonymous instance as a dictionary key will require the string to contain its escaped large body and is not recommended if you want to preserve the readability and editability of the JSON files.

Here is an example of JSON file for `Cat` and `Owner`:

```
# abigail.json
{
  "size": {
    "type": "Animal.Size",
    "fields": {
      "height": 10,
      "weight": 5
    }
  },
  "purr_type": "loud"
}

# alice.json
{
  "pet_nicknames": {
    "n:Cat:abigail": "abby",
    "n:Dog:alex": "ale"
  }
}

```


## Limitations

* Circular references in instances are not supported and currently lead to endless recursion
* Different struct types in different modules with same `__qualname__` currently lead to unwanted behavior
