from dataclasses import dataclass
from pathlib import Path

from gencode.ent_schema_generator import Config as SchemaConfig
from gencode.ent_schema_generator import EntSchemaGenerator


@dataclass
class Config:
    schemas_directory: str
    output_directory: str


class EntGenerator:
    config: Config

    def __init__(self, config: Config):
        self.config = config
        self.schemas_path = Path(self.config.schemas_directory).resolve()
        self.output_path = Path(self.config.output_directory).resolve()

    def run(self) -> None:
        print("EntGenerator is running...")
        print(f"Schemas directory: {self.schemas_path}")
        print(f"Output directory: {self.output_path}")

        # Create output directory if it doesn't exist
        self.output_path.mkdir(parents=True, exist_ok=True)

        schemas = self._load_schemas()
        print(f"Found {len(schemas)} schema(s).")

        for schema in schemas:
            print(f"Processing schema: {schema.schema_path}")
            EntSchemaGenerator(config=schema).run()

    def _load_schemas(self) -> list[SchemaConfig]:
        schema_files = list(self.schemas_path.glob("ent_*_schema.py"))
        return [
            SchemaConfig(
                schema_path=schema_file,
                output_path=self.output_path
                / f"{schema_file.stem.replace('_schema', '')}.py",
            )
            for schema_file in schema_files
        ]
