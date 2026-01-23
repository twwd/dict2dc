from dict2dc.models.base import UNTOUCHED


def test_untouched_type_as_bool():
    assert not UNTOUCHED


def test_untouched_type_as_str():
    assert str(UNTOUCHED) == "<UNTOUCHED>"
