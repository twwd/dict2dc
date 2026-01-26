# dict2dc - dictionary to dataclass parsing

![Python](https://img.shields.io/pypi/pyversions/dict2dc.svg)
[![PyPI version](https://img.shields.io/pypi/v/dict2dc.svg)](https://pypi.python.org/pypi/dict2dc)
[![Downloads](https://pepy.tech/badge/dict2dc)](https://pepy.tech/projects/dict2dc)
[![GitHub stars](https://img.shields.io/github/stars/twwd/dict2dc?style=flat)](https://github.com/twwd/dict2dc/stargazers)
[![last release status](https://github.com/twwd/dict2dc/actions/workflows/publish.yaml/badge.svg)](https://github.com/twwd/dict2dc/actions/workflows/publish.yaml)

`dict2dc` is a small Python library that helps to parse Python dicts to dataclass structures.
E.g., these dicts could originate from JSON deserialization.

The library supports nested dataclasses, collections and union types.
It always tries to initiate the best matching class.

## 🚀 Getting started

Install it in your Python project:

```shell
pip install dict2dc # or uv add or poetry add...
```

## 💻 Usage Examples

### Deserialization/Parsing

```python
import datetime
import dataclasses
from collections.abc import Collection
from dict2dc.dict2dc import Dict2Dc


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


data = {
    "a": 1,
    "b": ["Hello", "World"],  # JSON does not know sets thus they probably come as list
    "c": [{"a": "Hello"}, {"a": 42}],
    "d": "2026-01-26T10:33:48.703386",
}  # e.g., from json.load() or response.json()

Dict2Dc().from_dict_enforced(data, cls=MyDataClass)
```

### Serialization

#### JSON

```python
import dataclasses
import json
from dict2dc.dc2json import Dc2Json, DcJsonEncoder
from dict2dc.models.base import UNTOUCHED, UNTOUCHED_TYPE


@dataclasses.dataclass
class MyDataClass:
    a: str
    b: str | None = None
    c: int | UNTOUCHED_TYPE = UNTOUCHED  # Unmodified, the key will be omitted in the serializable dict


my_obj: MyDataClass = MyDataClass(a="Hello World")
serializable = Dc2Json().as_serializable(my_obj)
json.dumps(serializable)  # {"a": "Hello World", "b": None}

# Alternative
json.dumps(serializable, cls=DcJsonEncoder)
```

#### Query Parameters

```python
from dict2dc.dc2query import Dc2Query

my_obj: MyDataClass = MyDataClass(...)
query_params = Dc2Query().as_query_params(my_obj)
requests.get("https://example.com", params=query_params)
```

### 🛠️ Advanced Usage

The parsing has some opinionated defaults, e.g., regarding datetime representation.
If you want to adjust them or add your own parsing methods,
you can pass a mapping from target type to method to the constructor:

```python
import datetime
from dict2dc.dict2dc import Dict2Dc


def convert(v: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(float(v), tz=datetime.UTC)


dict2dc = Dict2Dc(
    special_conversions={
        datetime.datetime: convert
    }
)

dict2dc.from_dict_enforced(
    {
        "created": "1769416853"
    }, cls=MyDataClass
)
```

The default conversions can be found in [dict2dc.py](src/dict2dc/dict2dc.py#L22).
You can also use the optional `replace` parameter of the constructor to omit the default conversions entirely.  
*Note: These conversions are currently only triggered if the value to parse is a string.*

To adjust the serialization helpers (`Dc2Json`, `DcJsonEncoder`, `Dc2Query`),
you need to create your own subclasses.
There you can override the existing methods or add your own for custom conversions.