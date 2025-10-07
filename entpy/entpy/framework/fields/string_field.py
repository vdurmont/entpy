from __future__ import annotations

from entpy.framework.fields.core import (
    Field,
    FieldWithDefault,
    FieldWithDynamicExample,
    FieldWithExample,
)


class StringField(
    Field, FieldWithExample[str], FieldWithDynamicExample[str], FieldWithDefault[str]
):
    def __init__(self, name: str, length: int):
        super().__init__(name=name)
        self.length = length

    def get_python_type(self) -> str:
        return "str"

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None

    def generate_default(self) -> str | None:
        if self._default_value:
            return f'"{self._default_value}"'
        return None
