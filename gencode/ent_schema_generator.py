from dataclasses import dataclass
from pathlib import Path

from framework.ent_schema import EntSchema


@dataclass
class Config:
    schema_class: type[EntSchema]
    output_path: Path


class EntSchemaGenerator:
    config: Config
    base_name: str

    def __init__(self, config: Config):
        self.config = config
        self.base_name = self.config.schema_class.__name__.replace("Schema", "")

    def run(self) -> None:
        print(
            f"EntSchemaGenerator is running for {self.config.schema_class.__name__}..."
        )

        content = f"class {self.base_name}:\n    pass\n"

        # Write to output file
        with open(self.config.output_path, "w") as f:
            f.write(content)
