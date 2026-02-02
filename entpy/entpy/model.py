from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
