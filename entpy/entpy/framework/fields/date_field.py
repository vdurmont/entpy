from __future__ import annotations

from datetime import date

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)


class DateField(Field, FieldWithExample[date], FieldWithDynamicExample[date]):
    def get_python_type(self) -> str:
        return "date"

    def get_example_as_string(self) -> str | None:
        if self._example is None:
            return None
        return (
            f'date.fromisoformat("{self._example.isoformat()}")'
            if self._example is not None
            else None
        )
