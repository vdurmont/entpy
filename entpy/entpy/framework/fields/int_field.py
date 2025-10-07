from __future__ import annotations

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)


class IntField(Field, FieldWithExample[int], FieldWithDynamicExample[int]):
    def get_python_type(self) -> str:
        return "int"

    def get_example_as_string(self) -> str | None:
        return str(self._example) if self._example else None
