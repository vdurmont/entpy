import json
from collections.abc import Callable
from typing import Any
from uuid import UUID as PYUUID

from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.types import JSON as BaseJSON  # noqa: N811
from sqlalchemy.types import TypeDecorator, TypeEngine
from sqlalchemy.types import Uuid as BaseUuid


class Uuid(BaseUuid):
    def bind_processor(
        self, dialect: Dialect
    ) -> Callable[[PYUUID | None], str | None] | None:
        if dialect.supports_native_uuid and self.native_uuid:
            return None

        def process(value: PYUUID | None) -> str | None:
            return str(value) if value else None

        return process


class JSON(TypeDecorator[Any]):
    impl = BaseJSON
    cache_ok = True

    def __init__(self, length: int | None = None, *args: Any, **kwargs: Any) -> None:
        self.length = length
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB())
        return dialect.type_descriptor(BaseJSON())

    def bind_processor(self, dialect: Dialect) -> Callable[[Any | None], Any] | None:
        process_orig = super().bind_processor(dialect)
        length = self.length

        def process(value: Any | None) -> str | None:
            encoded = process_orig(value) if process_orig else json.dumps(value)
            if encoded is not None and length is not None and len(encoded) > length:
                raise ValueError(
                    f"Encoded JSON is {len(encoded)} characters, which exceeds the maximum of {length}"
                )
            return encoded

        return process
