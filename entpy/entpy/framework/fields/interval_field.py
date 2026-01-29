from __future__ import annotations

from datetime import timedelta

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)


class IntervalField(
    Field, FieldWithExample[timedelta], FieldWithDynamicExample[timedelta]
):
    def get_python_type(self) -> str:
        return "timedelta"

    def get_example_as_string(self) -> str | None:
        if self._example is None:
            return None
        return (
            f"timedelta(seconds={self._example.total_seconds()})"
            if self._example is not None
            else None
        )
