from abc import ABC, abstractmethod
from argparse import ArgumentParser
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable


def check_integer(v: str, *, conditions: Callable[[int], bool] = None) -> int:
    value = int(v)
    if conditions and not conditions(value):
        raise ValueError(value)
    return value


def check_integer_in_range(low: int | None, high: int | None) -> Callable[[str], int]:
    def is_in_range(n: int) -> bool:
        return (low is None or n >= low) and (high is None or n <= high)

    def check(v: str) -> int:
        return check_integer(v, conditions=is_in_range)

    return check


def parse_key_value_pair(value: str) -> tuple[str, str]:
    key, value = value.split("=", 1)
    return key, value


def try_parse_key_value_pair(value: str) -> str | tuple[str, str]:
    try:
        return parse_key_value_pair(value)
    except ValueError:
        return value


class ArgsParser(ABC):
    name: ClassVar[str]

    def __init__(self, parser: ArgumentParser) -> None:
        self._parser = parser
        self._parse_args()
        parser.set_defaults(func=self._run_command)

    @abstractmethod
    def _parse_args(self) -> None: ...

    @abstractmethod
    def _run_command(self, args: Namespace) -> None: ...


def run_command(*sub_parsers: type[ArgsParser]) -> None:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    for cls in sub_parsers:
        cls(subparsers.add_parser(cls.name))
    args = parser.parse_args()
    args.func(args)
