
from jungle.errors import ParseError

import enum


def parse_enum[T: enum.IntEnum](value: int, type: type[T]) -> T:
    if value not in type:
        raise ParseError(
            f"unrecognized enum value for {type.__name__}: {value}"
        )
    return type(value)

def parse_flags[T: enum.IntFlag](value: int, type: type[T]) -> T:
    instance = type(value)
    if instance.bit_count() != len(list(instance)):
        raise ParseError(
            f"unrecognized flag value for {type.__name__}: {value}"
        )
    return instance
