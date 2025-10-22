from __future__ import annotations

from typing import Self

from entpy.framework.fields.core import (
    Field,
    FieldValidator,
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

    def not_empty(self) -> Self:
        self._validators.append(NotEmptyStringValidator())
        return self

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None

    def generate_default(self) -> str | None:
        if self._default_value:
            return f'"{self._default_value}"'
        return None


class NotEmptyStringValidator(FieldValidator[str | None]):
    def validate(self, value: str | None) -> bool:
        return value is not None and value.strip() != ""
