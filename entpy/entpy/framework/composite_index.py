from dataclasses import dataclass


@dataclass
class CompositeIndex:
    field_names: list[str]
    unique: bool = False
    where: str | None = 'text("soft_deleted_at IS NULL")'
