from __future__ import annotations

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)


class BytesField(
    Field,
    FieldWithExample[bytes],
    FieldWithDynamicExample[bytes],
):
    def get_python_type(self) -> str:
        return "bytes"

    def get_example_as_string(self) -> str | None:
        if self._example is None:
            return None
        return f'bytes.fromhex("{self._example.hex()}")'
