from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping


@overload
def try_convert[T, R](cls: Callable[[T], R], val: T, *, default: R) -> R: ...


@overload
def try_convert[T, R](
    cls: Callable[[T], R], val: T, *, default: None = None
) -> R | None: ...


def try_convert[T, R](cls: Callable[[T], R], val: T, *, default: R = None) -> R | None:
    try:
        return cls(val)
    except ValueError:
        return default


def get_class_vars[T](cls: type, value_type: type[T]) -> Iterator[tuple[str, T]]:
    for k, c in cls.__dict__.items():
        if not k.startswith("_") and isinstance(c, value_type):
            yield k, c


def compose_number(numbers: Iterable[int]) -> int:
    return int("".join(str(n) for n in numbers))


def bits_to_int(items: Iterable[object]) -> int:
    """
    Convert boolean/int array -> number.

    >>> bits_to_int([True, False, 0, 1, "", 23, "je moeder"])
    75
    """
    return int("".join(f"{bool(i):b}" for i in items), 2)


def int_to_bits(i: int, *, zero_pad_to_length: int = 0) -> list[bool]:
    """
    Convert number -> boolean array.

    >>> int_to_bits(75)
    [True, False, False, True, False, True, True]
    >>> int_to_bits(75, zero_pad_to_length=10)
    [False, False, False, True, False, False, True, False, True, True]
    """
    s = f"{i:b}"
    if zero_pad_to_length:
        s = s.zfill(zero_pad_to_length)
    return [c == "1" for c in s]


def invert_dict[K, V](d: Mapping[K, V]) -> dict[V, K]:
    return {v: k for k, v in d.items()}


def grouped_by_key[K, V](pairs: Iterable[tuple[K, V]]) -> dict[K, list[V]]:
    """
    Group items by key(item).

    >>> grouped_by_key(
    ...     [
    ...         ("Alice", 3),
    ...         ("Bob", 6),
    ...         ("Charles", 4),
    ...         ("Alice", 8),
    ...         ("Charles", 5),
    ...         ("Bob", 2),
    ...         ("Charles", 7),
    ...         ("Alice", 9),
    ...         ("Charles", 1),
    ...     ]
    ... )
    {'Alice': [3, 8, 9], 'Bob': [6, 2], 'Charles': [4, 5, 7, 1]}
    """
    result: dict[K, list[V]] = {}
    for k, v in pairs:
        result.setdefault(k, []).append(v)
    return result
