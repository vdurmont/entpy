from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class FieldPreprocessor(ABC, Generic[T]):
    """
    A preprocessor normalizes a field's value on its way in. Where a validator
    inspects a value and rejects it, a preprocessor rewrites it -- stripping
    characters the column should never hold, folding case, and so on.

    It runs on the values the caller supplied, at the very start of a mutation:
    before the triggers, before the privacy check and before the validators. So
    a preprocessor cannot shape a value in a way that escapes authorization or
    validation, and everything downstream -- triggers, privacy rules, validators
    and the row itself -- sees the same normalized value.

    Preprocessors also run on the value passed to a unique lookup
    (`gen_from_xxxx`), so a field can be looked up with the same raw input it
    was written with. They are NOT applied to query filters: a
    `query(vc).where(...)` clause is passed to SQLAlchemy verbatim.

    A preprocessor is never called with `None`.
    """

    @abstractmethod
    def preprocess(self, value: T) -> T:
        pass
