from typing import TypeAlias, Union

import pytest

from dict2dc.utils.types import is_union

example_union_type: TypeAlias = None | int  # noqa: UP040
type example_union_type2 = None | int


@pytest.mark.parametrize(
    ("cls_", "expected"),
    [
        (None, False),
        (str, False),
        (int, False),
        (example_union_type, True),
        (example_union_type2, True),
        (str | bool, True),
        (Union[str, bool], True),  # noqa: UP007
        (list[str], False),
    ],
)
def test_is_union(cls_: type, expected: bool):
    assert is_union(cls_) == expected
