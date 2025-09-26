import subprocess
from importlib import import_module
from pathlib import Path

from framework.ent_schema import EntSchema
from gencode.ent_base_model_generator import generate as generate_base_model
from gencode.ent_schema_generator import generate as generate_schema


def run(schemas_directory: str, output_directory: str, base_import: str) -> None:
    print("EntGenerator is running...")
    schemas_path = Path(schemas_directory).resolve()
    output_path = Path(output_directory).resolve()
    print(f"Schemas directory: {schemas_path}")
    print(f"Output directory: {output_path}")

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate base model that all models will inherit from
    base_model = generate_base_model(base_import=base_import)
    _write_file(output_path / "ent_model.py", base_model)
    base_model_import = (
        "from" + str(output_path / "ent_model").replace("/", ".") + " import EntModel"
    )

    # Load all schemas to process
    configs = _load_schemas_configs(schemas_path=schemas_path, output_path=output_path)
    print(f"Found {len(configs)} schema(s).")

    # Gencode all the things!
    for config in configs:
        schema_class = config[0]
        schema_output_path = config[1]
        print(f"Processing schema: {schema_class.__name__}")
        code = generate_schema(
            schema_class=schema_class, ent_model_import=base_model_import
        )
        _write_file(schema_output_path, code)

    # Format the code before returning
    # TODO make this a config, not everyone uses ruff
    subprocess.run(["uv", "run", "ruff", "format", str(output_path)], check=True)
    subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", str(output_path)], check=True
    )

    print("EntGenerator has finished.")


def _load_schemas_configs(
    schemas_path: Path, output_path: Path
) -> list[tuple[type[EntSchema], Path]]:
    schema_files = list(schemas_path.glob("ent_*_schema.py"))

    for schema_file in schema_files:
        relative_path = schema_file.relative_to(Path.cwd())
        module_name = str(relative_path.with_suffix("")).replace("/", ".")
        import_module(module_name)

    schemas = EntSchema.__subclasses__()

    configs = []

    for schema_file in schema_files:
        schema_name = "".join(part.capitalize() for part in schema_file.stem.split("_"))
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
            (
                matching_schemas[0],
                output_path / f"{schema_file.stem.replace('_schema', '')}.py",
            )
        )

    return configs


def _write_file(path: Path, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)
