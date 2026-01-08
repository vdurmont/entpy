from __future__ import annotations

from entpy.framework.fields.core import (
    Field,
    FieldWithDefault,
    FieldWithDynamicExample,
    FieldWithExample,
)


class BoolField(
    Field, FieldWithExample[bool], FieldWithDynamicExample[bool], FieldWithDefault[bool]
):
    def get_python_type(self) -> str:
        return "bool"

    def get_example_as_string(self) -> str | None:
        if self._example is None:
            return None
        return "True" if self._example else "False"

    def generate_default(self) -> str | None:
        if self._default_value is not None:
            return f"{self._default_value}"
        return None

    def generate_sql_default(self) -> str | None:
        # SQL ALchemy expects lowercase defaults
        if self._default_value is not None:
            return f'"{self._default_value}"'.lower()
        return None
