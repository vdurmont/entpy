import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from entpy.framework.composite_index import CompositeIndex
from entpy.framework.fields.core import Field, FieldWithDefault

if TYPE_CHECKING:
    from entpy.framework.hooks import EntTrigger
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
        fields = [f for f in self.get_fields() if not f.is_deprecated]
        for pattern in self.get_patterns():
            fields += pattern.get_all_fields()
        return _sort_fields(fields)

    def get_composite_indexes(self) -> list[CompositeIndex]:
        return []

    def get_all_composite_indexes(self) -> list[CompositeIndex]:
        indexs = self.get_composite_indexes()
        for pattern in self.get_patterns():
            indexs += pattern.get_composite_indexes()
        return indexs

    def get_event_fields(self) -> list[str]:
        return []

    def get_triggers(self) -> list["EntTrigger"]:
        return []

    def get_description(self) -> str:
        return ""

    @classmethod
    def get_table_name(cls) -> str:
        base_name = (
            cls.__name__.removeprefix("Ent")
            .removesuffix("Schema")
            .removesuffix("Pattern")
        )

        # Convert CamelCase to snake_case
        # Insert underscore before uppercase letters (except first)
        base_name = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name)

        # Convert to lowercase
        return base_name.lower()

    @classmethod
    def get_table_schema(cls) -> str | None:
        return None

    @classmethod
    def get_qualified_table_name(cls) -> str:
        if cls.get_table_schema():
            return f"{cls.get_table_schema()}.{cls.get_table_name()}"
        return cls.get_table_name()


def _sort_fields(fields: list[Field]) -> list[Field]:
    # Separate nullable fields, fields with defaults, and non-nullable fields
    # We always process the mandatory fields first
    nullable_fields: list[Field] = []
    non_nullable_fields: list[Field] = []
    fields_with_default: list[Field] = []

    for f in fields:
        if isinstance(f, FieldWithDefault) and f.generate_default():
            fields_with_default.append(f)
        elif f.nullable:
            nullable_fields.append(f)
        else:
            non_nullable_fields.append(f)

    fields_with_default.sort(key=lambda f: f.name)
    nullable_fields.sort(key=lambda f: f.name)
    non_nullable_fields.sort(key=lambda f: f.name)

    return non_nullable_fields + fields_with_default + nullable_fields
