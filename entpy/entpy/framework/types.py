from collections.abc import Callable
from uuid import UUID as PYUUID

from sqlalchemy.engine import Dialect
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
