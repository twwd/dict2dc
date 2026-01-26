import collections.abc
import dataclasses
import datetime
import functools
import logging
from types import NoneType

import types
import typing
from collections.abc import Collection, Callable
from inspect import isabstract

from dict2dc.models.base import UNTOUCHED_TYPE
from dict2dc.models.parsing import DictToDataclassConversionError, FieldResult
from dict2dc.utils.types import is_union

D = typing.TypeVar("D")
D2 = typing.TypeVar("D2")

LOGGER = logging.getLogger("dict2dc")

DEFAULT_CONVERSION: dict[type, Callable[[typing.Any], typing.Any]] = {
    datetime.datetime: datetime.datetime.fromisoformat,
    datetime.date: datetime.date.fromisoformat,
    datetime.time: datetime.time.fromisoformat,
}


class Dict2Dc:
    """
    Our class to parse dicts to dataclasses.
    """

    def __init__(
        self, special_conversions: dict[type, Callable[[typing.Any], typing.Any]] | None = None, replace: bool = False
    ) -> None:
        """
        :param special_conversions: Special conversions for some types.
        :param replace: Whether the default conversions should be replaced or not updated.
        """
        self._special_conversions: dict[type, Callable[[typing.Any], typing.Any]] = (
            DEFAULT_CONVERSION.copy() if not replace else {}
        )
        if special_conversions is not None:
            self._special_conversions.update(special_conversions)
        super().__init__()

    @staticmethod
    def ensure_dataclass(obj: typing.Any):
        """
        Checks if the given object is a dataclass (or an instance) and raises a TypeError otherwise.

        :param obj: the object to check
        :raise TypeError if the given object is not a dataclass
        """
        if not dataclasses.is_dataclass(obj):
            raise TypeError(f"{obj} is not a dataclass")

    def _handle_field(self, field_name: str, field_value: typing.Any, cls_: type) -> FieldResult:  # noqa: PLR0911
        """
        :param field_name: the name of the field
        :param field_value: the value to check
        :param cls_: the type it should match
        :return: whether the value matches the given type
        """
        self._ensure_type(cls_)

        # if the type has a generic, isinstance does not work; thus we need the type without the generic
        # example: list[str] → list
        cls_without_generics = cls_
        while isinstance(cls_without_generics, types.GenericAlias):
            cls_without_generics = typing.get_origin(cls_without_generics)

        if dataclasses.is_dataclass(cls_):
            parsed_value = self._handle_dataclass(field_value, cls_)
            if parsed_value is not None:
                return parsed_value

        union_result = self._handle_union(field_name, field_value, cls_)
        if union_result is not None:
            return union_result

        sequence_result = self._handle_collection(field_value, field_name, cls_)
        if sequence_result is not None:
            return sequence_result

        if typing.get_origin(cls_) is typing.Literal:
            is_valid_literal = field_value in typing.get_args(cls_)
            return FieldResult(
                value=field_value,
                type_matches=is_valid_literal,
                matching_score=1 if is_valid_literal else 0,
                error=None
                if is_valid_literal
                else DictToDataclassConversionError.from_parsing_error(
                    field_name=field_name, field_type=cls_, field_value=field_value
                ),
            )

        special_class_result = self._handle_special_classes(cls_, field_value)
        if special_class_result is not None:
            return special_class_result

        constructor_result = self._handle_constructor(cls_, cls_without_generics, field_value)
        if constructor_result is not None:
            return constructor_result

        type_matches = isinstance(field_value, cls_without_generics)

        return FieldResult(
            value=field_value,
            type_matches=type_matches,
            matching_score=1 if type_matches else 0,
            error=None
            if type_matches
            else DictToDataclassConversionError.from_parsing_error(field_name, cls_, field_value),
        )

    def _handle_collection(self, field_value: typing.Any, field_name: str, cls_: type) -> FieldResult | None:
        type_origin: type | None = typing.get_origin(cls_)
        # typing.Literal is not a class that can be used with issubclass - don't know why
        if type_origin is not None and type_origin is not typing.Literal and issubclass(type_origin, Collection):
            is_concrete_type = not isabstract(type_origin)

            if isinstance(field_value, type_origin if is_concrete_type else Collection) or (
                # Special handling for tuples and sets:
                # In JSON, there is no representation for these, thus we convert them from lists.
                isinstance(field_value, list) and type_origin in (tuple, set)
            ):
                typing_args = typing.get_args(cls_)
                item_type = typing_args[0]

                # We currently support tuples that have an arbitrary length, but each element has the same type,
                # e.g., tuple[str, ...]
                # (see https://docs.python.org/3/library/typing.html#annotating-tuples)
                if len(typing_args) == 1 or (
                    type_origin is tuple and len(typing_args) == 2 and typing_args[1] is Ellipsis  # noqa: PLR2004
                ):
                    results: list[FieldResult] = [
                        self._handle_field(field_name=f"{field_name}[{idx}]", cls_=item_type, field_value=item)
                        for idx, item in enumerate(field_value)
                    ]
                    # All items must have the correct type
                    if not all(result.type_matches for result in results):
                        return FieldResult(
                            value=field_value,
                            type_matches=False,
                            error=DictToDataclassConversionError(
                                ", ".join(str(result.error) for result in results if result.error is not None),
                            ),
                        )

                    matching_score = 1 + sum(result.matching_score for result in results)
                    if is_concrete_type:
                        # noinspection PyArgumentList
                        return FieldResult(
                            value=type_origin(result.value for result in results),
                            type_matches=True,
                            matching_score=matching_score,
                        )
                    else:
                        # for backwards-compatibility,
                        # we return a list for a generic Collection or Sequence instead of a tuple
                        return FieldResult(
                            value=[result.value for result in results], type_matches=True, matching_score=matching_score
                        )
        # not applicable
        return None

    def _handle_dataclass(self, d: dict | None, cls_: type[D]) -> FieldResult | None:
        if d is None:
            return FieldResult(
                type_matches=False,
                error=DictToDataclassConversionError(
                    f'Field in unexpectedly None and thus cannot be parsed as "{cls_}"'
                ),
            )

        d_normalized = {}  # the parts of the dictionary that belong to the dataclass
        matching_score = 0
        for field in dataclasses.fields(cls_):
            is_required_field = field.default == dataclasses.MISSING and field.default_factory == dataclasses.MISSING
            field_name = field.name
            field_exists_in_d = field_name in d

            if not field_exists_in_d:
                field_exists_in_d = self._handle_space_in_key(d, field_name)

            # Ensure that a required field exists, ...
            if is_required_field and not field_exists_in_d:
                return FieldResult(
                    type_matches=False,
                    error=DictToDataclassConversionError(f'Required field "{field_name}" is missing'),
                )
            initial_field_value = d.get(field_name, None)
            field_value = initial_field_value
            # pyre-ignore[6]: pyre does not recognize a type as Hashable
            field_type = self._resolve_type(cls_, field)

            if field_exists_in_d:
                result = self._handle_field(field_name, field_value, field_type)
                matching_score += result.matching_score

                if not result.type_matches:
                    return FieldResult(
                        value=field_value,
                        type_matches=False,
                        error=DictToDataclassConversionError.from_parsing_error(field_name, field_type, field_value),
                    )

                d_normalized[field_name] = result.value

        return FieldResult(value=cls_(**d_normalized), type_matches=True, matching_score=matching_score)

    def _handle_union(self, field_name: str, field_value: typing.Any, cls_: type) -> FieldResult | None:
        if is_union(cls_):
            union_types = typing.get_args(cls_)

            # Special case: We've got empty dicts instead of None in some cases
            empty_dict_might_be_none = any(t is types.NoneType for t in union_types) and all(
                t is not dict for t in union_types
            )

            matching_values: list[FieldResult] = []
            for t in union_types:
                result = self._handle_field(field_name, field_value, t)
                if result.type_matches:
                    matching_values.append(result)
            if len(matching_values) > 0:
                # We use the best-fitting union type
                return max(matching_values, key=lambda r: r.matching_score)

            if empty_dict_might_be_none and isinstance(field_value, dict) and field_value == {}:
                return FieldResult(value=None, type_matches=True)

            return FieldResult(
                value=field_value,
                type_matches=False,
                error=DictToDataclassConversionError.from_parsing_error(field_name, cls_, field_value),
            )
        return None

    @staticmethod
    def _ensure_type(cls_: typing.Any):
        """
        Ensures that the given class is a type that we can handle.
        :param cls_: the thing to check
        :raise TypeError if we cannot handle this type
        """
        if not (
            isinstance(cls_, type)
            or is_union(cls_)
            or typing.get_origin(cls_) is typing.Literal
            or isinstance(cls_, types.GenericAlias)
        ):
            raise TypeError(f"Class parameter {cls_!r} of type {type(cls_)} is not a valid type.")

    @staticmethod
    def _handle_constructor(cls_: type, cls_without_generics: type, value: typing.Any) -> FieldResult | None:
        if (
            cls_ == UNTOUCHED_TYPE
            or issubclass(cls_without_generics, collections.abc.Iterable)
            or cls_ == NoneType
            or not isinstance(value, str)
        ):
            return None
        try:
            value = cls_(value)
            return FieldResult(value=value, type_matches=True, matching_score=1)
        except (ValueError, TypeError):
            LOGGER.debug("Value %s cannot be parsed as %s", value, cls_)
        return None

    def _handle_special_classes(self, cls_: type, value: typing.Any) -> FieldResult | None:
        # Try to parse date/time values
        if cls_ in self._special_conversions and isinstance(value, str):
            try:
                value = self._special_conversions[cls_](value)
                return FieldResult(value=value, type_matches=True, matching_score=1)
            except ValueError:
                LOGGER.debug("Value %s cannot be parsed as %s", value, cls_)
        return None

    def from_dict_enforced(self, d: dict | None, cls: type[D]) -> D:
        """
        Wrapper around `from_dict` for better type checking by skipping the None in the return type.

        :param d: the dict
        :param cls: the class to create
        :return: the instance of the class
        """
        result = self.from_dict(d, cls, enforce=True)
        # This is never the case since an exception is thrown in from_dict when enforce is set to True
        if result is None:
            raise ValueError("Illegal state")

        return result

    def from_dict(self, d: dict | None, cls: type[D], enforce=False) -> D | None:
        """
        Creates the given dataclass `cls` from the given dict
        if it contains all the required fields with the correct type.

        :param d: the dict
        :param cls: the class to create
        :param enforce: whether the given dict must be converted to the class and produce a TypeError otherwise.
                        When false, None is returned
        :return: the instance of the class if all required fields have been found, None otherwise
        """
        self.ensure_dataclass(cls)

        return self.from_any(d, cls, enforce=enforce)

    def from_any(self, d: typing.Any, cls: type[D], enforce=False) -> D:
        """
        Tries to create the given class `cls` from the given data.
        This class might be a dataclass, a list of such or some plain types.

        :param d: The data to parse.
        :param cls: The resulting class.
        :param enforce: Whether the given data must be converted to the class and produce a TypeError otherwise.
                        When false, None is returned.
        :return: The instance of the class if all required fields have been found, None otherwise.
        """
        result = self._handle_field(".", d, cls)

        if not result.type_matches:
            if not enforce:
                LOGGER.debug(
                    "The given dict could not be parsed as %s due to: %s. Provided dict was: %s", cls, result.error, d
                )
                return None

            raise TypeError(
                f"The given dict could not be parsed as {cls} due to: {result.error}. Provided dict was: {d}"
            )

        return result.value

    @staticmethod
    def _handle_space_in_key(d: dict, field_name: str) -> bool:
        # Sometimes, the JSON has a space ins keys that are probably mapped to underscores in the dataclasses.
        # Override this method if you need another handling.
        if "_" in field_name:
            field_name_with_spaces = field_name.replace("_", " ")
            if field_name_with_spaces in d:
                d[field_name] = d[field_name_with_spaces]
                return True
        return False

    def _handle_field_and_ensure_type(self, field_name: str, field_type: type, field_value: typing.Any):
        field_value, type_matches = self._handle_field(field_name, field_value, field_type)

        if not type_matches:
            raise DictToDataclassConversionError.from_parsing_error(field_name, field_type, field_value)

        return field_value, type_matches

    @functools.cache
    def _resolve_type(self, cls_: type | str, field: dataclasses.Field) -> type:
        """
        Resolves the type of the given class field.
        Returns the type of field if it is already a type.
        Otherwise, looks up the type hint on the class and returns the type of the class field.

        Background:
        If we use from __future__ import annotations (PEP 563 Postponed Evaluation of Annotations),
        we can use field types in our models before the classes are defined.
        This leads to the circumstance that dataclasses.field.type returns the type as string instead of the actual
        class reference.

        This operation is expensive, thus we cache the result.

        :param cls_: the class
        :param field: the field
        :return: the resolved type
        """
        field_type = field.type
        if isinstance(field_type, type):
            return field_type

        resolved = typing.get_type_hints(cls_)
        field_type = resolved[field.name]
        return field_type

    def map_to(self, d: D2, cls: type[D]) -> D | None:
        """
        Converts an instance of one dataclass to another.

        :param d: the instance of a dataclass that should be mapped
        :param cls: the type of the dataclass to which should be mapped
        :return: the mapped dataclass instance
        """
        self.ensure_dataclass(d)
        dataclass_as_dict = dataclasses.asdict(d)
        return self.from_dict(dataclass_as_dict, cls, enforce=True)
