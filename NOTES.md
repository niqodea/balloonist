# Notes

## Design question: Inflator-side vs Provider-side name-to-type resolution

Provider-side resolution would involve the usage of `.__subclasses__()` to build a hierarchy of providers so that each specialized provider can dispatch to the next one in the hierarchy.

* First approch
  \+ simple logic
  \+ arguably faster
  \- prohibits same-name classes
  \- not modular

* Second approach
  \+ allows some form of same-name classes, as long as name resolution happens within a narrow enough class scope
  \- complex
