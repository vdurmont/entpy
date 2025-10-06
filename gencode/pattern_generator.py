from framework.pattern import Pattern


def generate(
    pattern_class: type[Pattern],
) -> str:
    pattern = pattern_class()
    base_name = pattern_class.__name__.replace("Pattern", "")

    # Let's make sure that we require the properties for the pattern fields
    properties = ""
    for field in pattern.get_sorted_fields():
        properties += f"""
    @property
    @abstractmethod
    def {field.name}(self) -> {field.get_python_type()}:
        pass
"""

    return f"""
from abc import ABC, abstractmethod
from __future__ import annotations

class I{base_name}(ABC):
    {properties}
"""
