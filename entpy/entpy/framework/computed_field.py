from enum import Enum
from typing import Self

from entpy.framework.imported_object import ImportedObject
from entpy.framework.serialization import FieldSerialization


class ComputedField:
    """A serialized value that is not a column.

    `resolver` names an async function taking the ent and returning a value of
    `python_type`. It is referenced by import path rather than as a callable:
    the resolver imports the generated ent, so a schema importing it directly
    would import generated code.
    """

    name: str
    python_type: str
    resolver: ImportedObject
    description: str | None = None
    serialization: FieldSerialization | None = None

    def __init__(self, name: str, python_type: str, resolver: ImportedObject):
        self.name = name
        self.python_type = python_type
        self.resolver = resolver

    def documentation(self, doc: str) -> Self:
        self.description = doc
        return self

    def serialize(self, tier: Enum) -> Self:
        self.serialization = FieldSerialization(tier=tier)
        return self
