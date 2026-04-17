from __future__ import annotations

import inspect
import json
from typing import Any

from entpy.framework.fields.core import (
    Field,
    FieldWithDynamicExample,
    FieldWithExample,
)

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None  # type: ignore


class JsonField(
    Field,
    FieldWithExample[Any],
    FieldWithDynamicExample[Any],
):
    def __init__(self, name: str, expected_python_type: str | type[BaseModel]) -> None:
        super().__init__(name)
        # Detect if this is a Pydantic model
        if (
            BaseModel is not None
            and inspect.isclass(expected_python_type)
            and issubclass(expected_python_type, BaseModel)
        ):
            self._pydantic_model_class: type[BaseModel] | None = expected_python_type
            # Store the actual python type as dict[str, Any] for the database column
            self.expected_python_type = "dict[str, Any]"
        else:
            self._pydantic_model_class = None
            self.expected_python_type = expected_python_type  # type: ignore

    def get_python_type(self) -> str:
        return self.expected_python_type

    def is_pydantic_field(self) -> bool:
        """Check if this field uses a Pydantic model."""
        return self._pydantic_model_class is not None

    def get_pydantic_model_class(self) -> type[BaseModel] | None:
        """Get the Pydantic model class if this is a Pydantic field."""
        return self._pydantic_model_class

    def get_pydantic_type_string(self) -> str:
        """Get the fully qualified module.ClassName for the Pydantic model."""
        if not self._pydantic_model_class:
            return ""
        module = self._pydantic_model_class.__module__
        name = self._pydantic_model_class.__name__
        return f"{module}.{name}"

    def get_entity_property_type(self) -> str:
        """Get the type hint string for entity properties."""
        if self._pydantic_model_class:
            return self._pydantic_model_class.__name__
        return self.expected_python_type

    def get_pydantic_model_import(self) -> str | None:
        """Get the import statement for the Pydantic model."""
        if not self._pydantic_model_class:
            return None
        module = self._pydantic_model_class.__module__
        name = self._pydantic_model_class.__name__
        return f"from {module} import {name}"

    def get_example_as_string(self) -> str | None:
        if self._example is None:
            return None
        # If this is a Pydantic field and the example is a Pydantic instance
        if self._pydantic_model_class and isinstance(
            self._example, self._pydantic_model_class
        ):
            return self._example.model_dump_json()
        return json.dumps(self._example)
