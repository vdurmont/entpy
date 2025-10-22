from __future__ import annotations

from typing import Self

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)
from entpy.framework.fields.string_field import NotEmptyStringValidator


class TextField(Field, FieldWithExample[str], FieldWithDynamicExample[str]):
    def get_python_type(self) -> str:
        return "str"

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None

    def not_empty(self) -> Self:
        self._validators.append(NotEmptyStringValidator())
        return self
