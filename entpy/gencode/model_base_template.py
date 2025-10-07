def generate(base_import: str) -> str:
    return f"""
from datetime import datetime
from uuid import UUID as PYUUID

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

{base_import}


class EntModel(Base):
    __abstract__ = True

    @declared_attr
    def id(self) -> Mapped[PYUUID]:
        return mapped_column(
            UUID(as_uuid=True), primary_key=True, index=True, nullable=False
        )

    @declared_attr
    def created_at(self) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

    @declared_attr
    def updated_at(self) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            onupdate=func.now(),
            server_default=func.now(),
            nullable=False,
        )

    def __repr__(self) -> str:
        return f"<{{self.__class__.__name__}}({{self.id}})>"
"""
