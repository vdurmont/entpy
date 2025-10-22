from __future__ import annotations

from typing import Self

from entpy.framework.descriptor import Descriptor
from entpy.framework.fields.core import Field


class EdgeField(Field):
    edge_class: type[Descriptor]
    should_generate_example: bool = True

    def __init__(self, name: str, edge_class: type[Descriptor]):
        super().__init__(name=name, actual_name=name + "_id")
        self.edge_class = edge_class

    def get_python_type(self) -> str:
        return "UUID"

    def get_edge_type(self) -> str:
        classname = self.edge_class.__name__
        if classname.endswith("Pattern"):
            return "I" + classname.replace("Pattern", "")
        return classname.replace("Schema", "")

    def no_example(self) -> Self:
        self.should_generate_example = False
        return self
