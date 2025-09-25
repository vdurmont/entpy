from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    schema_path: Path
    output_path: Path


class EntSchemaGenerator:
    config: Config

    def __init__(self, config: Config):
        self.config = config

    def run(self) -> None:
        print("EntSchemaGenerator is running...")
        print(f"Schema path: {self.config.schema_path}")
        print(f"Output path: {self.config.output_path}")
