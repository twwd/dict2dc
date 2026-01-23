# A sentinel object to detect if a field of a patch request class was touched or not.
# This way we can distinguish if it is the default value None or if the field is explicitly set to None.
# noinspection PyPep8Naming
class UNTOUCHED_TYPE:  # noqa: N801
    def __str__(self):
        return "<UNTOUCHED>"

    def __repr__(self):
        return "<UNTOUCHED>"

    def __bool__(self):
        return False


UNTOUCHED = UNTOUCHED_TYPE()
