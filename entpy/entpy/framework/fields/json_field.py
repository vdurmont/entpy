from __future__ import annotations

import json
from typing import Any

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)


class JsonField(
    Field,
    FieldWithExample[Any],
    FieldWithDynamicExample[Any],
):
    def __init__(self, name: str, expected_python_type: str) -> None:
        super().__init__(name)
        self.expected_python_type = expected_python_type

    def get_python_type(self) -> str:
        return self.expected_python_type

    def get_example_as_string(self) -> str | None:
        return json.dumps(self._example) if self._example is not None else None
