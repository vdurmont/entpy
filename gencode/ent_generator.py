from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    schemas_directory: str
    output_directory: str


@dataclass
class EntGenerator:
    config: Config

    def run(self) -> None:
        print("Entity Generator is running...")
        schemas_path = Path(self.config.schemas_directory).resolve()
        output_path = Path(self.config.output_directory).resolve()
        print(f"Schemas directory: {schemas_path}")
        print(f"Output directory: {output_path}")
