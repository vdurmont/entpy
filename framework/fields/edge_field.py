from __future__ import annotations

from typing import TYPE_CHECKING, Self

from framework.fields.core import Field

if TYPE_CHECKING:
    from framework.ent_schema import EntSchema


class EdgeField(Field):
    edge_class: type[EntSchema]
    should_generate_example: bool = True

    def __init__(self, name: str, edge_class: type[EntSchema]):
        super().__init__(name=name, actual_name=name + "_id")
        self.edge_class = edge_class

    def get_python_type(self) -> str:
        return "UUID"

    def get_edge_type(self) -> str:
        return self.edge_class.__name__.replace("Schema", "")

    def no_example(self) -> Self:
        self.should_generate_example = False
        return self
