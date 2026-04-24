from __future__ import annotations

from entpy.framework.fields.core import FieldValidator
from entpy.framework.fields.string_field import StringField


class EmailField(StringField):
    def __init__(self, name: str, length: int = 255):
        super().__init__(name, length, case_sensitive=False)
        self._validators.append(EmailValidator())


class EmailValidator(FieldValidator[str | None]):
    def validate(self, value: str | None) -> tuple[bool, str | None]:
        if value is None:
            return (True, None)

        try:
            from email_validator import EmailNotValidError, validate_email

            validate_email(value, check_deliverability=False)
            return (True, None)
        except EmailNotValidError as e:
            return (False, f"Invalid email address: {str(e)}")
