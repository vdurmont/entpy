from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from framework.ent_schema import EntSchema
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

        configs = self._load_schemas_configs()
        print(f"Found {len(configs)} schema(s).")

        for config in configs:
            print(f"Processing schema: {config.schema_class.__name__}")
            EntSchemaGenerator(config=config).run()

    def _load_schemas_configs(self) -> list[SchemaConfig]:
        schema_files = list(self.schemas_path.glob("ent_*_schema.py"))

        for schema_file in schema_files:
            relative_path = schema_file.relative_to(Path.cwd())
            module_name = str(relative_path.with_suffix("")).replace("/", ".")
            import_module(module_name)

        schemas = EntSchema.__subclasses__()

        configs = []

        for schema_file in schema_files:
            schema_name = "".join(
                part.capitalize() for part in schema_file.stem.split("_")
            )
            matching_schemas = [
                schema for schema in schemas if schema.__name__ == schema_name
            ]
            if not matching_schemas:
                print(f"Warning: No matching schema class found for file {schema_file}")
                continue
            if len(matching_schemas) > 1:
                print(
                    "Warning: Multiple matching schema classes found for "
                    + f"file {schema_file}"
                )
                continue
            configs.append(
                SchemaConfig(
                    # Ignoring the type-abstract error because we ensure at runtime that
                    # schema_class is indeed a concrete subclass of EntSchema
                    schema_class=matching_schemas[0],  # type: ignore[type-abstract]
                    output_path=self.output_path
                    / f"{schema_file.stem.replace('_schema', '')}.py",
                )
            )

        return configs
