from __future__ import annotations

from entpy.framework.fields.core import (
    Field,
    FieldWithDefault,
    FieldWithDynamicExample,
    FieldWithExample,
)


class IntField(
    Field, FieldWithExample[int], FieldWithDynamicExample[int], FieldWithDefault[int]
):
    def get_python_type(self) -> str:
        return "int"

    def get_example_as_string(self) -> str | None:
        return str(self._example) if self._example is not None else None

    def generate_default(self) -> str | None:
        if self._default_value is not None:
            return f"{self._default_value}"
        return None

    def generate_sql_default(self) -> str | None:
        if self._default_value is not None:
            return f'"{self._default_value}"'
        return None
