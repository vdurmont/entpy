from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class FieldValidator(ABC, Generic[T]):
    @abstractmethod
    def validate(self, value: T) -> bool:
        pass
