import dataclasses
import datetime

from dict2dc.dc2query import Dc2Query
from dict2dc.models.base import UNTOUCHED_TYPE, UNTOUCHED


@dataclasses.dataclass
class TestDataClassForQueryParameters:
    id: int
    updated: datetime.datetime
    active: bool
    other_ids: list[int] = dataclasses.field(default_factory=list)
    tags: set[str] = dataclasses.field(default_factory=set)
    untouched: UNTOUCHED_TYPE = UNTOUCHED
    none: None = None


def test_convert_to_query_parameters():
    date = "2023-10-10T05:13:35.425665+00:00"
    parsed_date = datetime.datetime.fromisoformat(date)
    given = TestDataClassForQueryParameters(
        id=42, updated=parsed_date, active=True, tags={"b", "f", "a"}, other_ids=[110, 14, 53]
    )

    actual = Dc2Query().as_query_params(given)

    expected = {"id": 42, "updated": date, "active": "true", "tags": "a,b,f", "other_ids": "110,14,53"}

    assert actual == expected
