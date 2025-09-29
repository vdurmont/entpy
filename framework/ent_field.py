from __future__ import annotations

from abc import ABC, abstractmethod


class EntField(ABC):
    name: str
    nullable: bool = True

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_python_type(self) -> str:
        raise NotImplementedError("Subclasses must implement get_python_type")

    def not_null(self) -> EntField:
        self.nullable = False
        return self


class StringField(EntField):
    def __init__(self, name: str, length: int):
        super().__init__(name=name)
        self.length = length

    def get_python_type(self) -> str:
        return "str"
