from datetime import datetime

from pydantic import BaseModel


class ChildComputedItem(BaseModel):
    shout: str


class ChildComputedDetailed(ChildComputedItem):
    name_length: int


class TopComputedItem(BaseModel):
    label: str
    computed_at: datetime
