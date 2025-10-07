from entpy import Schema
from entpy.gencode.base_generator import generate as generate_base
from entpy.gencode.example_generator import generate as generate_example
from entpy.gencode.model_generator import generate as generate_model
from entpy.gencode.mutator_generator import generate as generate_mutator


def generate(
    schema_class: type[Schema],
    ent_model_import: str,
    session_getter_import: str,
    session_getter_fn_name: str,
    vc_import: str,
    vc_name: str,
) -> str:
    schema = schema_class()
    base_name = schema_class.__name__.replace("Schema", "")

    model_content = generate_model(schema=schema, base_name=base_name)
    base_content = generate_base(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
        vc_name=vc_name,
    )
    mutator_content = generate_mutator(
        schema=schema,
        base_name=base_name,
        session_getter_fn_name=session_getter_fn_name,
        vc_name=vc_name,
    )
    example_content = generate_example(
        schema=schema, base_name=base_name, vc_name=vc_name
    )

    imports = (
        [ent_model_import]
        + model_content.imports
        + base_content.imports
        + mutator_content.imports
        + example_content.imports
    )
    imports = list(set(imports))  # Remove duplicates
    imports_code = "\n".join(imports)

    return f"""
from __future__ import annotations
from entpy import ViewerContext, Ent
from uuid import UUID, uuid4
from datetime import datetime
{vc_import}
{session_getter_import}
{imports_code}

{model_content.code}

{base_content.code}

{mutator_content.code}

{example_content.code}
"""
