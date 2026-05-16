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
    def __init__(self, name: str, length: int, case_sensitive: bool = True):
        super().__init__(name=name)
        self.length = length
        self.case_sensitive = case_sensitive
        self._validators.append(MaxLengthValidator(length))

    def get_python_type(self) -> str:
        return "str"

    def not_empty(self) -> Self:
        self._validators.append(NotEmptyStringValidator())
        return self

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None

    def generate_default(self) -> str | None:
        if self._default_value is not None:
            return f'"{self._default_value}"'
        return None


class MaxLengthValidator(FieldValidator[str | None]):
    def __init__(self, max_length: int):
        self.max_length = max_length

    def validate(self, value: str | None) -> tuple[bool, str | None]:
        if value is None:
            return (True, None)
        if len(value) > self.max_length:
            return (
                False,
                f"Value exceeds maximum length of {self.max_length} characters",
            )
        return (True, None)


class NotEmptyStringValidator(FieldValidator[str | None]):
    def validate(self, value: str | None) -> tuple[bool, str | None]:
        is_valid = value is not None and value.strip() != ""
        return (is_valid, "Field cannot be empty" if not is_valid else None)
