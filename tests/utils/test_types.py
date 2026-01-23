from typing import TypeAlias

import pytest

from dict2dc.utils.types import is_union

example_union_type: TypeAlias = None | int


@pytest.mark.parametrize(
    ("cls_", "expected"),
    [
        (None, False),
        (str, False),
        (int, False),
        (example_union_type, True),
        (str | bool, True),
        (list[str], False),
    ],
)
def test_is_union(cls_: type, expected: bool):
    assert is_union(cls_) == expected
