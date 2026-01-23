from collections.abc import Iterable
from typing import TypeAlias

# Use dict with str key as a pragmatic type that does not confuse the type checker
_ParamsMappingValueType: TypeAlias = str | bytes | int | float | Iterable[str | bytes | int | float] | None
Params: TypeAlias = dict[str, _ParamsMappingValueType]
