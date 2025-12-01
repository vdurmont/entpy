import subprocess
from hashlib import sha256
from importlib import import_module
from pathlib import Path

from entpy import Pattern, Schema
from entpy.gencode.ent_query_template import generate as generate_ent_query
from entpy.gencode.model_base_template import generate as generate_base_model
from entpy.gencode.pattern_generator import generate as generate_pattern
from entpy.gencode.schema_generator import generate as generate_schema
from entpy.gencode.view_generator import generate as generate_view


def run(
    schemas_directory: str,
    output_directory: str,
    base_import: str,
    session_getter_import: str,
    session_getter_fn_name: str,
    vc_import: str,
    vc_name: str,
) -> None:
    print("EntGenerator is running...")
    schemas_path = Path(schemas_directory).resolve()
    output_path = Path(output_directory).resolve()
    print(f"Schemas directory: {schemas_path}")
    print(f"Output directory: {output_path}")

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate base model that all models will inherit from, and the ent_query
    base_model = generate_base_model(base_import=base_import)
    _write_file(output_path / "ent_model.py", base_model)
    ent_query = generate_ent_query()
    _write_file(output_path / "ent_query.py", ent_query)

    # Load all descriptors to process
    configs = _load_descriptors_configs(
        schemas_path=schemas_path, output_path=output_path
    )
    print(f"Found {len(configs)} schema(s) and pattern(s).")

    # Gencode all the things!
    models_list = ""
    models_list_mapping = ""
    for config in configs:
        descriptor_class = config[0]
        descriptor_output_path = config[1]
        print(f"Processing: {descriptor_class.__name__}")
        if issubclass(descriptor_class, Schema):
            base_name = descriptor_class.__name__.replace("Schema", "")
            uuid_type = sha256(base_name.encode()).digest()[:2]
            uuid_hex = "".join(f"\\x{b:02x}" for b in uuid_type)
            models_list_mapping += f'\n    b"{uuid_hex}": {base_name},'
            models_list += f"\nfrom .{descriptor_output_path.stem} import {base_name}Model  # noqa: F401"  # noqa: E501
            models_list += f"\nfrom .{descriptor_output_path.stem} import {base_name}"
            code = generate_schema(
                schema_class=descriptor_class,
                ent_model_import="from .ent_model import EntModel",
                session_getter_import=session_getter_import,
                session_getter_fn_name=session_getter_fn_name,
                vc_import=vc_import,
                vc_name=vc_name,
            )
        elif issubclass(descriptor_class, Pattern):
            children = get_children_schema_classes(
                pattern_class=descriptor_class,
            )
            code = generate_pattern(
                pattern_class=descriptor_class,
                children_schema_classes=children,
                ent_model_import="from .ent_model import EntModel",
                session_getter_import=session_getter_import,
                session_getter_fn_name=session_getter_fn_name,
                vc_import=vc_import,
                vc_name=vc_name,
            )
            view_code = generate_view(
                pattern_class=descriptor_class, children_schema_classes=children
            )
            _write_file(
                descriptor_output_path.with_stem(f"{descriptor_output_path.stem}_view"),
                view_code,
            )
            models_list += (
                "\nfrom ."
                + descriptor_output_path.stem
                + "_view import "
                + descriptor_class.__name__.replace("Pattern", "View")
                + "  # noqa: F401"
            )
        else:
            raise TypeError(f"Unknown descriptor type: {descriptor_class}")
        _write_file(descriptor_output_path, code)

    models_list_code = f"""
from entpy import Ent
{vc_import}
{models_list}

UUID_TO_ENT: dict[bytes, type[Ent[{vc_name}]]] = {{
{models_list_mapping}
}}
"""
    _write_file(output_path / "all_models.py", models_list_code)

    # Format the code before returning
    # TODO make this a config, not everyone uses ruff
    subprocess.run(["uv", "run", "ruff", "format", str(output_path)], check=True)
    subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", str(output_path)], check=True
    )

    print("EntGenerator has finished.")


def _load_descriptors_configs(
    schemas_path: Path, output_path: Path
) -> list[tuple[type[Schema] | type[Pattern], Path]]:
    schema_files = list(schemas_path.glob("ent_*_schema.py"))
    pattern_files = list(schemas_path.glob("ent_*_pattern.py"))

    for descriptor_file in schema_files + pattern_files:
        relative_path = descriptor_file.relative_to(Path.cwd())
        module_name = str(relative_path.with_suffix("")).replace("/", ".")
        import_module(module_name)

    schemas = Schema.__subclasses__()
    patterns = Pattern.__subclasses__()

    configs = []

    for descriptor_file in schema_files + pattern_files:
        descriptor_name = "".join(
            part.capitalize() for part in descriptor_file.stem.split("_")
        )
        matching_descriptors = [
            schema for schema in schemas if schema.__name__ == descriptor_name
        ] + [pattern for pattern in patterns if pattern.__name__ == descriptor_name]
        if not matching_descriptors:
            print(
                f"Warning: No matching descriptor class found for file {descriptor_file}"  # noqa: E501
            )
            continue
        if len(matching_descriptors) > 1:
            print(
                "Warning: Multiple matching descriptor classes found for "
                + f"file {descriptor_file}"
            )
            continue
        configs.append(
            (
                matching_descriptors[0],
                output_path
                / f"{descriptor_file.stem.replace('_schema', '').replace('_pattern', '')}.py",  # noqa: E501
            )
        )

    # Sort configs by descriptor class name for stable output
    configs.sort(key=lambda config: config[0].__name__)

    return configs


def _write_file(path: Path, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def get_children_schema_classes(pattern_class: type[Pattern]) -> list[type[Schema]]:
    schema_classes = Schema.__subclasses__()
    result = []
    for schema_class in schema_classes:
        # Safe to ignore the typing error here: we're not instantiating the base
        # class and all subclasses implement the right functions
        sch = schema_class()  # type: ignore
        patterns = sch.get_patterns()
        for pattern in patterns:
            if isinstance(pattern, pattern_class):
                result.append(schema_class)
    # Sort by class name for deterministic ordering
    result.sort(key=lambda schema: schema.__name__)
    return result
