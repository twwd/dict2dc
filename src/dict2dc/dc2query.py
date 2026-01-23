import dataclasses
import datetime
import typing
from functools import singledispatchmethod

from dict2dc.models.base import UNTOUCHED_TYPE
from dict2dc.models.requests import Params

D = typing.TypeVar("D")


class Dc2Query:
    """
    Converts a dataclass into a dictionary that can be used as query parameters for requests.
    """

    def as_query_params(self, obj: D | None) -> Params | None:
        """
        Converts a dataclass into a dictionary that can be used as query parameters for requests.
        It can only handle dataclasses that are not nested.
        It strips None and UNTOUCHED values.

        :param obj: the dataclass instance
        :return: the dictionary
        """
        if obj is None:
            return None
        obj_as_dict = dataclasses.asdict(obj)
        keys = set(obj_as_dict.keys())
        for key in keys:
            value = obj_as_dict[key]

            if value is None or isinstance(value, UNTOUCHED_TYPE):
                # Ignore None and untouched
                obj_as_dict.pop(key)
                continue
            else:
                updated_value = self._convert(value)

            obj_as_dict[key] = updated_value

        return obj_as_dict

    @singledispatchmethod
    def _convert(self, value: typing.Any) -> typing.Any:
        return value

    @_convert.register(bool)
    def _(self, value: bool) -> str:
        return str(value).lower()

    @_convert.register(datetime.date)
    @_convert.register(datetime.time)
    @_convert.register(datetime.datetime)
    def _(self, value: datetime.date | datetime.time | datetime.datetime) -> str:
        return value.isoformat()

    @_convert.register(set)
    def _(self, value: set) -> str | None:
        return ",".join(list(sorted(map(str, value))))

    @_convert.register(list)
    def _(self, value: list) -> str:
        return ",".join(map(str, value))
