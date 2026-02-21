from __future__ import annotations

from typing import Self

from entpy.framework.fields.core import (
    Field,
    FieldValidator,
    FieldWithDefault,
    FieldWithDynamicExample,
    FieldWithExample,
)


class EmailField(
    Field, FieldWithExample[str], FieldWithDynamicExample[str], FieldWithDefault[str]
):
    def __init__(self, name: str, length: int = 255):
        super().__init__(name=name)
        self.length = length
        self._validators.append(EmailValidator())

    def get_python_type(self) -> str:
        return "str"

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None

    def generate_default(self) -> str | None:
        if self._default_value:
            return f'"{self._default_value}"'
        return None


class EmailValidator(FieldValidator[str | None]):
    def validate(self, value: str | None) -> bool:
        if value is None:
            return True

        try:
            from email_validator import EmailNotValidError, validate_email

            validate_email(value, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
