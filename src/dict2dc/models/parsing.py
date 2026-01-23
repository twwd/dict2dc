import dataclasses
import typing


class DictToDataclassConversionError(Exception):
    """
    An internal exception that might be thrown during the conversion of a dict to a dataclass in ~from_dict.
    """

    @classmethod
    def from_parsing_error(
        cls, field_name: str, field_type: type, field_value: typing.Any
    ) -> "DictToDataclassConversionError":
        return cls(f'Field "{field_name}" with type "{field_type}" cannot be parsed from "{field_value}"')


@dataclasses.dataclass
class FieldResult:
    """
    The (updated/parsed) value for the field.
    """

    value: typing.Any | None = None

    """
    Whether the value matches the field type.
    """
    type_matches: bool = False

    """
    How many sub fields have been parsed (without default values)
    """
    matching_score: int = 0

    """
    The error when the value does not match the field type.
    """
    error: DictToDataclassConversionError | None = None
