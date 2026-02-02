from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, Self, TypeVar

from .validator import FieldValidator

T = TypeVar("T")


class Field(ABC, Generic[T]):
    name: str
    original_name: str
    nullable: bool = True
    is_unique: bool = False
    is_indexed: bool = False
    is_immutable: bool = False
    description: str | None = None
    _validators: list[FieldValidator[T]]

    def __init__(self, name: str, actual_name: str | None = None):
        self.original_name = name
        self.name = actual_name if actual_name else name
        self._validators = []

    @abstractmethod
    def get_python_type(self) -> str:
        raise NotImplementedError("Subclasses must implement get_python_type")

    def not_null(self) -> Self:
        self.nullable = False
        return self

    def unique(self) -> Self:
        self.is_unique = True
        return self

    def index(self) -> Self:
        self.is_indexed = True
        return self

    def documentation(self, doc: str) -> Self:
        self.description = doc
        return self

    def immutable(self) -> Self:
        self.is_immutable = True
        return self

    def validators(self, validators: list[FieldValidator[T]]) -> Self:
        self._validators = self._validators + validators
        return self


class FieldWithExample(ABC, Generic[T]):
    _example: T | None = None

    def example(self: Self, example: T) -> Self:
        self._example = example
        return self

    def get_example(self: Self) -> T | None:
        return self._example

    @abstractmethod
    def get_example_as_string(self) -> str | None:
        pass


class FieldWithDynamicExample(ABC, Generic[T]):
    _generator: Callable[..., T] | None = None

    def dynamic_example(self: Self, generator: Callable[..., T]) -> Self:
        self._generator = generator
        return self

    def get_example_generator(self: Self) -> Callable[..., T] | None:
        return self._generator


class FieldWithDefault(ABC, Generic[T]):
    _default_value: T | None = None

    def default(self: Self, default_value: T) -> Self:
        self._default_value = default_value
        return self

    @abstractmethod
    def generate_default(self: Self) -> str | None:
        pass

    def generate_sql_default(self: Self) -> str | None:
        return self.generate_default()
