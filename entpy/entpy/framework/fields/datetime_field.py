from __future__ import annotations

from datetime import datetime

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)


class DatetimeField(
    Field, FieldWithExample[datetime], FieldWithDynamicExample[datetime]
):
    def get_python_type(self) -> str:
        return "datetime"

    def get_example_as_string(self) -> str | None:
        if self._example is None:
            return None
        return (
            f'datetime.fromisoformat("{self._example.isoformat()}")'
            if self._example is not None
            else None
        )
