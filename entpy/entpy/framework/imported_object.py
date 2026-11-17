from dataclasses import dataclass


@dataclass(frozen=True)
class ImportedObject:
    module: str
    name: str

    def __str__(self) -> str:
        return f"from {self.module} import {self.name}"
