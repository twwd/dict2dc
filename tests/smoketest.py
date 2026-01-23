import dataclasses
import json
import sys

from dict2dc.dc2json import Dc2Json, DcJsonEncoder
from dict2dc.dc2query import Dc2Query
from dict2dc.dict2dc import Dict2Dc


@dataclasses.dataclass
class ADataclass:
    a: int
    b: str | None


def main():
    d = {
        "a": 1,
        "b": "2",
    }

    instance = Dict2Dc().from_dict_enforced(d, ADataclass)

    serialized = Dc2Json().as_serializable(instance)

    if not serialized == d:
        return 40

    print(json.dumps(instance, cls=DcJsonEncoder))

    print(Dc2Query().as_query_params(instance))

    print("Smoke test was successful")

    return 0


if __name__ == "__main__":
    sys.exit(main())
