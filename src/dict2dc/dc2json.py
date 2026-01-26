import dataclasses
import datetime
import decimal
import json
import typing
import uuid
from functools import singledispatchmethod

UNSERIALIZABLE = object()


class Dc2Json:
    """
    Methods to transform an object to a JSON-serializable data structure.
    Heavily inspired from https://stackoverflow.com/a/51674892
    """

    @singledispatchmethod
    def as_serializable(self, obj: typing.Any):
        """
        Filter and transform a Python object to only include serializable object types

        In dictionaries, keys are converted to strings.

        :param obj: The object to serialize
        """

        # Dataclasses have no specific type, thus they must be handled here :(
        if dataclasses.is_dataclass(obj):
            return self.as_serializable(dataclasses.asdict(obj))

        # default handler, called for anything without a specific
        # type registration.
        return UNSERIALIZABLE

    @as_serializable.register(dict)
    def _handle_dict(self, d: dict):
        converted = ((str(k), self.as_serializable(v)) for k, v in d.items())
        return {k: v for k, v in converted if v is not UNSERIALIZABLE}

    @as_serializable.register(list)
    @as_serializable.register(tuple)
    def _handle_sequence(self, seq: list | tuple):
        converted = (self.as_serializable(v) for v in seq)
        return [v for v in converted if v is not UNSERIALIZABLE]

    @as_serializable.register(set)
    def _handle_set(self, seq: set):
        converted = [self.as_serializable(v) for v in seq]
        # Try to sort the set
        try:
            converted = sorted(converted)
        except TypeError:
            pass
        return [v for v in converted if v is not UNSERIALIZABLE]

    @as_serializable.register(datetime.date)
    @as_serializable.register(datetime.time)
    @as_serializable.register(datetime.datetime)
    def _handle_date_and_time(self, value: datetime.date | datetime.time | datetime.datetime):
        return value.isoformat()

    @as_serializable.register(decimal.Decimal)
    def _handle_decimal(self, value: decimal.Decimal):
        # Return Decimals as strings
        return f"{value:.2f}"

    @as_serializable.register(uuid.UUID)
    def _handle_uuid(self, value: uuid.UUID):
        return str(value)

    @as_serializable.register(int)
    @as_serializable.register(float)
    @as_serializable.register(str)
    @as_serializable.register(bool)  # redundant, supported as int subclass
    @as_serializable.register(type(None))
    def _handle_default_scalar_types(self, value):
        return value


class DcJsonEncoder(json.JSONEncoder):
    """
    JSONEncoder that can handle Dataclasses, date, time, datetime, and our UNTOUCHED_TYPE.
    """

    dc2json = Dc2Json()

    def default(self, obj):
        return self.dc2json.as_serializable(obj)
