import subprocess
from importlib import import_module
from pathlib import Path

from entpy import Pattern, Schema
from entpy.gencode.model_base_template import generate as generate_base_model
from entpy.gencode.pattern_generator import generate as generate_pattern
from entpy.gencode.schema_generator import generate as generate_schema
from entpy.gencode.utils import ImportedObject, to_snake_case
from entpy.gencode.view_generator import generate as generate_view


def run(
    schemas_directory: str,
    output_directory: str,
    base_model_import: str,
    vc: ImportedObject,
    privacy_mixin: ImportedObject | None = None,
    threshold_to_stop_loading_ents_for_count: int = 50,
) -> None:
    print("EntGenerator is running...")
    schemas_path = Path(schemas_directory).resolve()
    output_path = Path(output_directory).resolve()
    print(f"Schemas directory: {schemas_path}")
    print(f"Output directory: {output_path}")

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    base_model = generate_base_model(base_import=base_model_import)
    _write_file(output_path / "ent_model.py", base_model)

    # Load all descriptors to process
    configs = _load_descriptors_configs(
        schemas_path=schemas_path, output_path=output_path
    )
    print(f"Found {len(configs)} schema(s) and pattern(s).")

    # Gencode all the things!
    examples_list_imports = ""
    examples_list = ""
    models_list_imports = ""
    models_list_mapping = ""
    id_type_mappings_imports = ""
    id_type_mappings_types = ""
    id_type_mappings_types_to_ents = ""
    for config in configs:
        descriptor_class = config[0]
        descriptor_output_path = config[1]
        print(f"Processing: {descriptor_class.__name__}")
        if issubclass(descriptor_class, Schema):
            base_name = descriptor_class.__name__.removesuffix("Schema")
            uuid_type = descriptor_class.get_uuid_type()
            uuid_hex = "".join(f"\\x{b:02x}" for b in uuid_type)
            models_list_mapping += f'\n    b"{uuid_hex}": {base_name},'
            models_list_imports += f"\nfrom .{descriptor_output_path.stem} import {base_name}Model  # noqa: F401"  # noqa: E501
            models_list_imports += (
                f"\nfrom .{descriptor_output_path.stem} import {base_name}"
            )
            id_type_mappings_imports += (
                f"\nfrom .{descriptor_output_path.stem} import {base_name}"
            )
            id_type_mappings_types += f"\n_{to_snake_case(base_name)}_type = sha256({base_name}.__name__.encode()).digest()[:2]"
            id_type_mappings_types_to_ents += (
                f"\n_{to_snake_case(base_name)}_type: {base_name},"
            )
            examples_list_imports += (
                f"from .{descriptor_output_path.stem} import {base_name}Example\n"
            )
            examples_list += f"    {base_name}Example,\n"
            code = generate_schema(
                schema_class=descriptor_class,
                vc=vc,
                threshold_to_stop_loading_ents_for_count=threshold_to_stop_loading_ents_for_count,
                privacy_mixin=privacy_mixin,
            )
        elif issubclass(descriptor_class, Pattern):
            children = get_children_schema_classes(
                pattern_class=descriptor_class,
            )
            code = generate_pattern(
                pattern_class=descriptor_class,
                children_schema_classes=children,
                vc=vc,
                threshold_to_stop_loading_ents_for_count=threshold_to_stop_loading_ents_for_count,
            )
            view_code = generate_view(
                pattern_class=descriptor_class,
                children_schema_classes=children,
                base_import=base_model_import,
            )
            _write_file(
                descriptor_output_path.with_stem(f"{descriptor_output_path.stem}_view"),
                view_code,
            )
            models_list_imports += (
                "\nfrom ."
                + descriptor_output_path.stem
                + "_view import "
                + descriptor_output_path.stem
                + "_view  # noqa: F401"
            )
        else:
            raise TypeError(f"Unknown descriptor type: {descriptor_class}")

        _write_file(descriptor_output_path, code)

    models_list_code = f"""
from entpy import Ent

{vc}
from .ent_model import EntModel
{models_list_imports}

UUID_TO_ENT: dict[bytes, type[Ent[{vc.name}, EntModel]]] = {{
{models_list_mapping}
}}
"""
    _write_file(output_path / "all_models.py", models_list_code)

    id_type_mappings_code = f"""
from hashlib import sha256
from uuid import UUID

from entpy import Ent

{id_type_mappings_imports}

# Compute type identifiers (first 2 bytes of SHA256 of class name)
{id_type_mappings_types}

# Map type bytes to Ent classes
ID_TYPE_MAPPING: dict[bytes, type] = {{
{id_type_mappings_types_to_ents}
}}
"""
    _write_file(output_path / "all_id_types.py", id_type_mappings_code)

    examples_list_code = f"""
{examples_list_imports}

examples = [
{examples_list}
]
"""
    _write_file(output_path / "all_examples.py", examples_list_code)

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
                / f"{descriptor_file.stem.removesuffix('_schema').removesuffix('_pattern')}.py",  # noqa: E501
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
