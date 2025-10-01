from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Self, TypeVar


class EntField(ABC):
    name: str
    nullable: bool = True

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_python_type(self) -> str:
        raise NotImplementedError("Subclasses must implement get_python_type")

    def not_null(self) -> Self:
        self.nullable = False
        return self


T = TypeVar("T")


class EntFieldWithExample(ABC, Generic[T]):
    _example: T | None = None

    def example(self: Self, example: T) -> Self:
        self._example = example
        return self

    def has_example(self) -> bool:
        return self._example is not None

    def getx_example(self: Self) -> T:
        if not self._example:
            raise ValueError("No example has been set.")
        return self._example

    @abstractmethod
    def get_example_as_string(self) -> str:
        pass


class StringField(EntField, EntFieldWithExample[str]):
    def __init__(self, name: str, length: int):
        super().__init__(name=name)
        self.length = length

    def get_python_type(self) -> str:
        return "str"

    def get_example_as_string(self) -> str:
        return f'"{self._example}"'
