from __future__ import annotations

from typing import Self

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)
from entpy.framework.fields.string_field import (
    NotEmptyStringValidator,
    RemoveNullBytesPreprocessor,
)


class TextField(Field, FieldWithExample[str], FieldWithDynamicExample[str]):
    def __init__(self, name: str, case_sensitive: bool = True):
        super().__init__(name=name)
        self.case_sensitive = case_sensitive
        self._preprocessors.append(RemoveNullBytesPreprocessor())

    def get_python_type(self) -> str:
        return "str"

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None

    def not_empty(self) -> Self:
        self._validators.append(NotEmptyStringValidator())
        return self
