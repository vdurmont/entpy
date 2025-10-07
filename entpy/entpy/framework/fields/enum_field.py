from __future__ import annotations

from enum import Enum
from typing import TypeVar

from entpy.framework.fields.core import (
    Field,
    FieldWithDefault,
    FieldWithDynamicExample,
    FieldWithExample,
)

T = TypeVar("T", bound="Enum")


class EnumField(
    Field, FieldWithExample[T], FieldWithDynamicExample[T], FieldWithDefault[T]
):
    def __init__(self, name: str, enum_class: type[T]):
        super().__init__(name=name)
        self.enum_class = enum_class

    def get_python_type(self) -> str:
        return self.enum_class.__name__

    def get_example_as_string(self) -> str | None:
        return f"{self._example}" if self._example else None

    def generate_default(self) -> str | None:
        if self._default_value:
            return f"{self._default_value}.value"
        return None
