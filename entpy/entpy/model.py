from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    field_serializer,
)


class APIEntity(BaseModel):
    model_config = ConfigDict(
        allow_inf_nan=False, from_attributes=True, ser_json_bytes="base64"
    )

    id: UUID = Field(..., description="Unique identifier for the entity")
    created_at: datetime = Field(
        ..., description="Timestamp when the entity was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the entity was last updated"
    )
    soft_deleted_at: datetime | None = Field(
        ..., description="Timestamp when the entity was soft deleted"
    )


class TieredAPIEntity(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, ser_json_bytes="base64")

    id: UUID = Field(..., description="Unique identifier for the entity")
    entity_type: str = Field(..., description="The class name of the entity")
    created_at: AwareDatetime = Field(
        ..., description="Timestamp when the entity was created"
    )
    updated_at: AwareDatetime = Field(
        ..., description="Timestamp when the entity was last updated"
    )
    soft_deleted_at: AwareDatetime | None = Field(
        ..., description="Timestamp when the entity was soft deleted"
    )

    # Pydantic writes UTC as "Z"; this keeps Python's own "+00:00" form.
    @field_serializer("*", mode="wrap", when_used="json")
    def _serialize_datetime(
        self, value: Any, handler: SerializerFunctionWrapHandler
    ) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        # The handler would serialize a nested model as its declared type and
        # drop the fields of the concrete one.
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        return handler(value)
