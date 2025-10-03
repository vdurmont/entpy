from abc import ABC, abstractmethod

from framework.fields.core import Field


class EntSchema(ABC):
    @abstractmethod
    def get_fields(self) -> list[Field]:
        pass

    def get_sorted_fields(self) -> list[Field]:
        # Separate nullable and non-nullable fields
        # We always process the mandatory fields first
        nullable_fields = [f for f in self.get_fields() if f.nullable]
        nullable_fields.sort(key=lambda f: f.name)
        non_nullable_fields = [f for f in self.get_fields() if not f.nullable]
        non_nullable_fields.sort(key=lambda f: f.name)
        return non_nullable_fields + nullable_fields
