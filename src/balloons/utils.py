from typing import Generic, Iterable, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class FrozenDict(Generic[K, V]):
    def __init__(self, data: dict[K, V]) -> None:
        self._data = data

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FrozenDict):
            return False
        return self._data == other._data

    def __hash__(self) -> int:
        return hash(frozenset(self._data.items()))

    def __repr__(self) -> str:
        return f"FrozenDict({self._data})"

    def __str__(self) -> str:
        return str(self._data)

    def values(self) -> Iterable[V]:
        return self._data.values()

    def items(self) -> Iterable[tuple[K, V]]:
        return self._data.items()
