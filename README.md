# balloons

A Python library that deflates dataclasses into a compact database of JSON files and inflates them back into fully referenced objects, ensuring minimal data duplication.

## Concept

### The problem

The most straightforward way to deserialize Python dataclasses is to convert them to dictionaries and dump their contents as JSON.

For example:

```py
abigail = Cat(size=Size(height=10, weight=5), purr_type="loud")
bella = Dog(size=Size(height=25, weight=15) obedience=0.7)
carol = Owner(pets=[abigail, bella])

Path("abigail.json").write_text(json.dumps(asdict(abigail)))
Path("bella.json").write_text(json.dumps(asdict(bella)))
Path("carol.json").write_text(json.dumps(asdict(carol)))
```

The Python code above will generate the following JSON files:

```
# abigail.json
{
  "size": {
    "height": 10,
    "weight": 5
  },
  "purr_type": "loud"
}

# bella.json
{
  "size": {
    "height": 25,
    "weight": 15
  },
  obedience: 0.7
}

# carol.json
{
  "pets": [
    {
      "size": {
        "height": 10,
        "weight": 5
      },
      "purr_type": "loud"
    },
    {
      "size": {
        "height": 20,
        "weight": 10
      },
      "purr_type": "soft"
    }
  ]
}
```

While these JSONs might suffice in some scenarios, they exhibit some potentially unwanted traits.
For instance, data is duplicated across files, such as the attributes of the pets, which can lead to inconsistencies if you were to update the files.
Additionally, if you want to deserialize their contents back to their runtime equivalents, instantiating the correct class and preserving object references can be challenging or even impossible.

### Proposed approach

balloons introduces the `Balloon` and `NamedBalloon` base classes.

* `Balloon` objects are frozen dataclass objects that can be handled by the balloons API for deflation and inflation.
* `NamedBalloon` objects also include a `name` field that acts as the identifier of the object within all objects of its class.
   Every `Balloon` object can be promoted to a `NamedBalloon` with the `to_named` method.

The library deflates `NamedBalloon` objects into JSON files, storing them efficiently for easy future inflation.
The serialization includes class names, enabling correct instantiation.
References to `NamedBalloon` objects within other objects are stored as a class-name and object-name pair.
This approach preserves object references and prevents data duplication.

Storing objects with the balloons API is easy thanks to the `Balloonist` type:

```py
# We now also specify names to obtain named balloons
abigail = Cat(size=Size(height=10, weight=5), purr_type="loud").to_named("abigail")
bella = Dog(size=Size(height=25, weight=15) obedience=0.7).to_named("bella")
carol = Owner(pets=[abigail, bella]).to_named("carol")

# Assuming suitable balloonist objects are in scope
animal_balloonist.track(abigail)
animal_balloonist.track(benjamin)
owner_balloonist.track(carol)
```

with the resulting JSON files appearing in the database:

```
# Cat/abigail.json
{
  "size": {
    "type": "Size",
    "fields": {
      "height": 10,
      "weight": 5
    }
  },
  "purr_type": "loud"
}

# Dog/bella.json
{
  "size": {
    "type": "Size",
    "fields": {
      "height": 25,
      "weight": 15
    }
  },
  "obedience": 0.7
}

# Owner/carol.json
{
  "pets": [
    "Cat:abigail",
    "Dog:bella"
  ]
}
```

The format of the data now enables efficient inflation that takes into account object references.

Here is how you can retrieve the objects, again using `Balloonist`:

```py
# In another Python session...
abigail = animal_balloonist.get("abigail")
bella = animal_balloonist.get("bella")
carol = owner_balloonist.get("carol")

assert isinstance(abigail, Cat)
assert isinstance(bella, Dog)
assert isinstance(carol, Owner)

assert abigail.name == "abigail"
assert abigail.size == Size(height=10, weight=5)
assert abigail.purr_type == "loud"

# Not just equals, they're the same objects in memory!
assert carol.pets[0] is abigail
assert carol.pets[1] is bella
```

## Limitations

* All balloon types must have a unique `__qualname__` for this library to work correctly
* Circular object references are not supported
