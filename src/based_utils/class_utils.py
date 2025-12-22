from functools import cached_property
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Sortable(Protocol):
    def __lt__(self, other: Self) -> bool: ...


class Unique:
    def __init__(self, data: Sortable) -> None:
        self.data = data

    def __lt__(self, other: Self) -> bool:
        return self.data < other.data

    def __repr__(self) -> str:
        return repr(self.data)


class WithClearablePropertyCache:
    def clear_property_cache(self) -> None:
        """
        Invalidate all cached properties.

        (so they will be recomputed the first time they're accessed again).
        """
        cls = self.__class__
        cache = self.__dict__
        for attr in list(cache.keys()):
            if isinstance(getattr(cls, attr, None), cached_property):
                del cache[attr]


def get_class_vars[T](cls: type, value_type: type[T]) -> dict[str, T]:
    return {
        name: v
        for name, v in cls.__dict__.items()
        if not name.startswith("_") and isinstance(v, value_type)
    }
