from dataclasses import dataclass


@dataclass
class CompositeIndex:
    name: str
    field_names: list[str]
    unique: bool = False
