import dataclasses
import datetime
import decimal
import json
import uuid

import pytest

from dict2dc.dc2json import UNSERIALIZABLE, Dc2Json, DcJsonEncoder
from dict2dc.models.base import UNTOUCHED, UNTOUCHED_TYPE

DATETIME_STRING = "2023-10-10T05:13:35.123456+00:00"
DATETIME = datetime.datetime(2023, 10, 10, 5, 13, 35, microsecond=123456, tzinfo=datetime.timezone.utc)


@dataclasses.dataclass
class TestDataSubClass:
    name: str


@dataclasses.dataclass
class TestDataClassSimple:
    active: bool
    child: TestDataSubClass | None = None


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


@pytest.mark.parametrize(
    ["given", "expected"],
    [
        (1, 1),
        (None, None),
        ("TEST", "TEST"),
        (UNTOUCHED, UNSERIALIZABLE),
        ([1, "ABC", UNTOUCHED], [1, "ABC"]),
        ({1: "A", "B": UNTOUCHED}, {"1": "A"}),
        (DATETIME, DATETIME_STRING),
        ([{"A": {"b", "c", "a"}}, 42], [{"A": ["a", "b", "c"]}, 42]),
        (TestDataClassSimple(True, TestDataSubClass("CHILD")), {"active": True, "child": {"name": "CHILD"}}),
        (decimal.Decimal("47.11"), "47.11"),
    ],
)
def test_json_serializable(given, expected):
    assert Dc2Json().as_serializable(given) == expected


def test_dataclass_json_encoder():
    date = "2023-10-10T05:13:35.425665+00:00"
    parsed_date = datetime.datetime.fromisoformat(date)
    given = TestDataClass(
        id=42, updated=parsed_date, active=True, tags={"a", "f", "b"}, child=TestDataSubClass(name="NAME")
    )

    actual = json.dumps(given, cls=DcJsonEncoder)

    expected = (
        f'{{"id": 42, "updated": "{date}", '
        f'"active": true, "child": {{"name": "NAME"}}, "description": null, "tags": ["a", "b", "f"]}}'
    )

    assert actual == expected


def test_dataclass_json_encoder__given_a_value_for_a_otherwise_untouched_field():
    given = TestDataClass(id=42, updated=DATETIME, active=True, another_field=42)

    actual = json.dumps(given, cls=DcJsonEncoder)

    expected = (
        f'{{"id": 42, "updated": "{DATETIME_STRING}", '
        f'"active": true, "child": null, "description": null, "tags": [], "another_field": 42}}'
    )

    assert actual == expected
