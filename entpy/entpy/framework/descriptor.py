from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from entpy.framework.errors import ExecutionError
from entpy.framework.fields.core import Field

if TYPE_CHECKING:
    from entpy.framework.pattern import Pattern


class Descriptor(ABC):
    """
    A descriptor is a class that describes how an Ent should be handled.
    It might be abstract (Pattern) or concrete (Schema).
    """

    @abstractmethod
    def get_fields(self) -> list[Field]:
        pass

    def get_patterns(self) -> list["Pattern"]:
        return []

    def get_sorted_fields(self) -> list[Field]:
        return _sort_fields(self.get_fields())

    def get_all_fields(self) -> list[Field]:
        # First gather all the fields
        fields = self.get_fields()
        for pattern in self.get_patterns():
            fields += pattern.get_all_fields()
        return _sort_fields(fields)

    def get_description(self) -> str:
        return ""

    def _get_field(self, field_name: str) -> Field:
        for field in self.get_fields():
            if field.name == field_name or field.original_name == field_name:
                return field
        raise ExecutionError(
            f"Cannot find field {field_name} in {self.__class__.__name__}"
        )


def _sort_fields(fields: list[Field]) -> list[Field]:
    # Separate nullable and non-nullable fields
    # We always process the mandatory fields first
    nullable_fields = [f for f in fields if f.nullable]
    nullable_fields.sort(key=lambda f: f.name)
    non_nullable_fields = [f for f in fields if not f.nullable]
    non_nullable_fields.sort(key=lambda f: f.name)
    return non_nullable_fields + nullable_fields
