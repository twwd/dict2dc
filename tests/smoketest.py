import dataclasses
import json
import sys
import datetime
from collections.abc import Collection

from dict2dc.dc2json import Dc2Json, DcJsonEncoder
from dict2dc.dc2query import Dc2Query
from dict2dc.dict2dc import Dict2Dc


@dataclasses.dataclass(frozen=True)
class MyDataSubClass1:
    a: str


@dataclasses.dataclass(frozen=True)
class MyDataSubClass2:
    a: int


@dataclasses.dataclass
class MyDataClass:
    a: int
    b: set[str]
    c: Collection[MyDataSubClass1 | MyDataSubClass2] = dataclasses.field(default_factory=list)
    d: datetime.datetime | None = None


def main():
    d = {
        "a": 1,
        "b": ["Hello", "World"],  # JSON does not know sets thus they probably come as list
        "c": [{"a": "Hello"}, {"a": 42}],
        "d": "2026-01-26T10:33:48.703386",
    }

    instance = Dict2Dc().from_dict_enforced(d, MyDataClass)

    serialized = Dc2Json().as_serializable(instance)

    if not serialized == d:
        return 40

    print(json.dumps(instance, cls=DcJsonEncoder))

    print(Dc2Query().as_query_params(instance))

    print("Smoke test was successful")

    return 0


if __name__ == "__main__":
    sys.exit(main())
