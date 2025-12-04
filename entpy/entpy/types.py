from datetime import UTC, datetime
from typing import Any

from sqlalchemy.engine import Dialect
from sqlalchemy.types import TIMESTAMP, TypeDecorator


class DateTime(TypeDecorator):
    impl = TIMESTAMP
    cache_ok = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, timezone=True, **kwargs)

    def process_bind_param(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")

        # Ensure that timestamps are stored in UTC for SQLite
        return value.astimezone(UTC)

    def process_result_value(
        self, value: datetime | None, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return None

        # SQLite doesn't store timezones so we need to make this timezone-aware
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value
