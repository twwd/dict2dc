from collections.abc import Iterable

# Use dict with str key as a pragmatic type that does not confuse the type checker
type _ParamsMappingValueType = str | bytes | int | float | Iterable[str | bytes | int | float] | None
type Params = dict[str, _ParamsMappingValueType]
