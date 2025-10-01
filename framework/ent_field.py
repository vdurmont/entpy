from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, Self, TypeVar


class EntField(ABC):
    name: str
    nullable: bool = True
    is_unique: bool = False

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_python_type(self) -> str:
        raise NotImplementedError("Subclasses must implement get_python_type")

    def not_null(self) -> Self:
        self.nullable = False
        return self

    def unique(self) -> Self:
        self.is_unique = True
        return self


T = TypeVar("T")


class EntFieldWithExample(ABC, Generic[T]):
    _example: T | None = None

    def example(self: Self, example: T) -> Self:
        self._example = example
        return self

    def get_example(self: Self) -> T | None:
        return self._example

    @abstractmethod
    def get_example_as_string(self) -> str | None:
        pass


class EntFieldWithDynamicExample(ABC, Generic[T]):
    _generator: Callable[..., T] | None = None

    def dynamic_example(self: Self, generator: Callable[..., T]) -> Self:
        self._generator = generator
        return self

    def get_example_generator(self: Self) -> Callable[..., T] | None:
        return self._generator


class StringField(EntField, EntFieldWithExample[str], EntFieldWithDynamicExample[str]):
    def __init__(self, name: str, length: int):
        super().__init__(name=name)
        self.length = length

    def get_python_type(self) -> str:
        return "str"

    def get_example_as_string(self) -> str | None:
        return f'"{self._example}"' if self._example else None
