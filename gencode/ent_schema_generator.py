from framework.ent_schema import EntSchema
from gencode.ent_base_generator import generate as generate_base
from gencode.ent_model_generator import generate as generate_model


def generate(
    schema_class: type[EntSchema], ent_model_import: str, session_getter_import: str
) -> str:
    schema = schema_class()
    base_name = schema_class.__name__.replace("Schema", "")

    model_content = generate_model(schema=schema, base_name=base_name)
    base_content = generate_base(
        schema=schema, base_name=base_name, session_getter_import=session_getter_import
    )

    imports = [ent_model_import] + model_content.imports + base_content.imports
    imports = list(set(imports))  # Remove duplicates
    imports_code = "\n".join(imports)

    return f"""
from __future__ import annotations
{imports_code}

{model_content.code}

{base_content.code}
"""
