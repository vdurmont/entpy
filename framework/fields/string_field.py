from __future__ import annotations

from framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)


class StringField(Field, FieldWithExample[str], FieldWithDynamicExample[str]):
    def __init__(self, name: str, length: int):
        super().__init__(name=name)
        self.length = length

    def get_python_type(self) -> str:
        return "str"

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None
