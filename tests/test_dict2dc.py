import dataclasses
import datetime
import decimal
import uuid
from collections.abc import Sequence, Collection
from typing import Literal

import pytest

from dict2dc.dict2dc import Dict2Dc
from dict2dc.models.base import UNTOUCHED, UNTOUCHED_TYPE


@pytest.fixture
def uut():
    return Dict2Dc()


@dataclasses.dataclass
class TestDataSubClass:
    name: str


@dataclasses.dataclass
class TestDataClass:
    id: int
    updated: datetime.datetime
    active: bool
    child: TestDataSubClass | None = None
    description: str | None = None
    tags: set[str] = dataclasses.field(default_factory=set)
    another_field: int | UNTOUCHED_TYPE = UNTOUCHED
    decimal_field: decimal.Decimal | UNTOUCHED_TYPE = UNTOUCHED
    uuid_field: uuid.UUID | UNTOUCHED_TYPE = UNTOUCHED


@dataclasses.dataclass
class TestDataClassWithSequence:
    id: int
    children: Sequence[TestDataSubClass] | None = None


@dataclasses.dataclass
class TestDataClassWithTuple:
    id: int
    children: tuple[TestDataSubClass, ...]


def test_from_dict(uut: Dict2Dc):
    given = {"id": 42, "updated": "2023-09-29T06:25:42.517+00:00", "active": False}

    actual = uut.from_dict(given, TestDataClass)

    assert isinstance(actual, TestDataClass)
    assert actual.id == 42
    assert not actual.active


def test_from_dict__given_set_as_list(uut: Dict2Dc):
    given = {"id": 42, "updated": "2023-09-29T06:25:42.517+00:00", "active": False, "tags": ["a", "b", "c"]}

    actual = uut.from_dict(given, TestDataClass)

    assert isinstance(actual, TestDataClass)
    assert actual.id == 42
    assert actual.tags == {"a", "b", "c"}


def test_from_dict__given_space_in_key(uut: Dict2Dc):
    given = {"id": 42, "updated": "2023-09-29T06:25:42.517+00:00", "active": False, "another field": 42}

    actual = uut.from_dict(given, TestDataClass)

    assert isinstance(actual, TestDataClass)
    assert actual.id == 42
    assert not actual.active
    assert actual.another_field == 42


def test_from_dict__given_invalid_type(uut: Dict2Dc):
    given = {"id": "ID", "updated": "2023-09-29T06:25:42.517+00:00", "active": True}

    actual = uut.from_dict(given, TestDataClass)

    assert actual is None


def test_from_dict__give_invalid_type__when_enforce_flag_is_set(uut: Dict2Dc):
    given = {
        "id": 42,
        "updated": "2023-09-29T06:25:42.517+00:00",
        "child": {"a": "b"},
    }

    with pytest.raises(TypeError) as exc_info:
        uut.from_dict(given, TestDataClass, enforce=True)

    assert exc_info.type is TypeError


def test_from_dict__given_decimal(uut: Dict2Dc):
    given = {"id": 42, "updated": "2023-09-29T06:25:42.517+00:00", "active": False, "decimal_field": "47.11"}

    actual = uut.from_dict(given, TestDataClass)

    assert isinstance(actual, TestDataClass)
    assert actual.id == 42
    assert actual.decimal_field == decimal.Decimal("47.11")


def test_from_dict__given_uuid(uut: Dict2Dc):
    uuid_val = uuid.uuid4()
    given = {"id": 42, "updated": "2023-09-29T06:25:42.517+00:00", "active": False, "uuid_field": str(uuid_val)}

    actual = uut.from_dict(given, TestDataClass)

    assert isinstance(actual, TestDataClass)
    assert actual.id == 42
    assert actual.uuid_field == uuid_val


def test_from_dict__given_nested(uut: Dict2Dc):
    given = {"id": 42, "updated": "2023-09-29T06:25:42.517+00:00", "active": False, "child": {"name": "NAME"}}

    actual = uut.from_dict(given, TestDataClass)

    assert isinstance(actual, TestDataClass)
    assert actual.id == 42
    assert not actual.active
    assert isinstance(actual.child, TestDataSubClass)
    assert actual.child.name == "NAME"


def test_from_dict__given_nested_with_empty_dict_instead_of_none(uut: Dict2Dc):
    given = {"id": 42, "updated": "2023-09-29T06:25:42.517+00:00", "active": False, "child": {}}

    actual = uut.from_dict(given, TestDataClass)

    assert isinstance(actual, TestDataClass)
    assert actual.id == 42
    assert actual.child is None


def test_from_dict__given_nested_sequence(uut: Dict2Dc):
    given = {"id": 4711, "children": [{"name": "1"}, {"name": "2"}]}

    actual = uut.from_dict(given, TestDataClassWithSequence)

    assert isinstance(actual, TestDataClassWithSequence)
    assert actual.id == 4711
    assert len(actual.children) == 2
    assert isinstance(actual.children[0], TestDataSubClass)
    assert actual.children[0].name == "1"
    assert isinstance(actual.children[1], TestDataSubClass)
    assert actual.children[1].name == "2"


def test_from_dict__given_nested_sequence_with_invalid_type(uut: Dict2Dc):
    given = {"id": 4711, "children": [{"title": "1"}, {"name": "2"}]}

    with pytest.raises(TypeError) as exc_info:
        uut.from_dict(given, TestDataClassWithSequence, enforce=True)

    assert exc_info.type is TypeError


@pytest.mark.parametrize(
    ["given"],
    (
        ({"id": 4711, "children": [{"name": "1"}, {"name": "2"}]},),
        ({"id": 4711, "children": ({"name": "1"}, {"name": "2"})},),
    ),
)
def test_from_dict__given_nested_tuple(uut: Dict2Dc, given):
    actual = uut.from_dict(given, TestDataClassWithTuple)

    assert isinstance(actual, TestDataClassWithTuple)
    assert actual.id == 4711
    assert len(actual.children) == 2
    assert isinstance(actual.children[0], TestDataSubClass)
    assert actual.children[0].name == "1"
    assert isinstance(actual.children[1], TestDataSubClass)
    assert actual.children[1].name == "2"


@dataclasses.dataclass
class DataclassStrAndList:
    persons: list[str] | str


def test_from_dict__given_str_and_list(
    uut: Dict2Dc,
):
    actual1 = uut.from_dict({"persons": "single"}, DataclassStrAndList)
    actual2 = uut.from_dict({"persons": ["multiple1", "multiple2"]}, DataclassStrAndList)

    assert isinstance(actual1.persons, str)
    assert isinstance(actual2.persons, list)
    assert len(actual2.persons) == 2


@dataclasses.dataclass
class DataclassLiteral:
    kind: Literal["a", "b", "c"]


def test_from_dict__given_literal(
    uut: Dict2Dc,
):
    actual = uut.from_dict({"kind": "a"}, DataclassLiteral)

    assert isinstance(actual, DataclassLiteral)
    assert isinstance(actual.kind, str)
    assert actual.kind == "a"


@dataclasses.dataclass
class UnionTypeA:
    a: str | None = None


@dataclasses.dataclass
class UnionTypeB:
    b: str | None = None


@dataclasses.dataclass
class DataclassWithUnion:
    child: UnionTypeA | UnionTypeB


@dataclasses.dataclass
class DataclassWithUnionReversed:
    child: UnionTypeB | UnionTypeA


@pytest.mark.parametrize(
    ("data", "cls", "expected"),
    [
        ({"child": {"b": "VALUE"}}, DataclassWithUnion, DataclassWithUnion(child=UnionTypeB(b="VALUE"))),
        ({"child": {"a": "VALUE"}}, DataclassWithUnion, DataclassWithUnion(child=UnionTypeA(a="VALUE"))),
        ({"child": {"b": None}}, DataclassWithUnion, DataclassWithUnion(child=UnionTypeB(b=None))),
        ({"child": {"a": None}}, DataclassWithUnion, DataclassWithUnion(child=UnionTypeA(a=None))),
        ({"child": {}}, DataclassWithUnion, DataclassWithUnion(child=UnionTypeA())),
        ({"child": {}}, DataclassWithUnionReversed, DataclassWithUnionReversed(child=UnionTypeB())),
    ],
)
def test_from_dict__given_multiple_fitting_union_types(uut: Dict2Dc, data, cls, expected):
    actual = uut.from_dict(data, cls)
    assert actual == expected


@dataclasses.dataclass
class ChildWithOptionalValue:
    a: str | None = None


@dataclasses.dataclass
class DataclassWithOptionalChild:
    child: ChildWithOptionalValue | None = None


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"child": None}, DataclassWithOptionalChild()),
        ({"child": {}}, DataclassWithOptionalChild(ChildWithOptionalValue())),
    ],
)
def test_from_dict__given_datclass_with_optional_child(uut: Dict2Dc, data, expected):
    actual = uut.from_dict(data, DataclassWithOptionalChild)
    assert actual == expected


def test_from_any__given_list_of_dataclasses(uut: Dict2Dc):
    expected = [TestDataSubClass(name="NAME1"), TestDataSubClass(name="NAME2"), TestDataClassWithSequence(id=3), None]

    data = [
        {
            "name": "NAME1",
        },
        {
            "name": "NAME2",
        },
        {
            "id": 3,
        },
        None,
    ]

    actual = uut.from_any(data, Collection[TestDataSubClass | TestDataClassWithSequence | None], enforce=True)
    assert actual == expected


@dataclasses.dataclass
class InputChild:
    id: int
    name: str


@dataclasses.dataclass
class Input:
    id: int
    name: str
    child: InputChild


@dataclasses.dataclass
class OutputChild:
    name: str | None = None


@dataclasses.dataclass
class Output:
    name: str = ""
    child: OutputChild | None = None


def test_map_to(
    uut: Dict2Dc,
):
    given = Input(42, "PARENT", InputChild(4711, "CHILD"))

    actual = uut.map_to(given, Output)

    assert isinstance(actual, Output)
    assert actual.name == "PARENT"
    assert actual.child.name == "CHILD"
