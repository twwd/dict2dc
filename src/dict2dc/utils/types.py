from types import UnionType
from typing import TypeVar, Union, get_origin

T = TypeVar("T")


def is_union(t: type) -> bool:
    """
    Borrowed from https://stackoverflow.com/a/74546180

    :param t: the type to check
    :return: whether the type is a union type
    """
    origin = get_origin(t)
    return origin is Union or origin is UnionType
