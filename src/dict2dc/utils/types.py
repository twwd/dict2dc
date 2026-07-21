import types
import typing

T = typing.TypeVar("T")


def is_union(t: type) -> bool:
    """
    :param t: the type to check
    :return: whether the type is a union type
    """
    # Unwrap PEP 695 `type` statement aliases
    if isinstance(t, typing.TypeAliasType):
        t = t.__value__

    # X | Y syntax (Python 3.10+)
    if isinstance(t, types.UnionType):
        return True

    # typing.Union[X, Y]
    return typing.get_origin(t) is typing.Union
