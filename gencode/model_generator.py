import re

from framework.fields.edge_field import EdgeField
from framework.fields.string_field import StringField
from framework.schema import Schema
from gencode.generated_content import GeneratedContent
from gencode.utils import to_snake_case


def generate(schema: Schema, base_name: str) -> GeneratedContent:
    fields = schema.get_all_fields()

    fields_code = ""
    edges_imports = []
    for field in fields:
        common_column_attributes = ", nullable=" + (
            "True" if field.nullable else "False"
        )
        common_column_attributes += ", unique=True" if field.is_unique else ""

        if isinstance(field, StringField):
            mapped_type = "str | None" if field.nullable else "str"
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += (
                f"mapped_column(String({field.length}){common_column_attributes})\n"
            )
        elif isinstance(field, EdgeField):
            edge_base_name = field.edge_class.__name__.replace("Schema", "")
            edge_filename = to_snake_case(edge_base_name)
            edges_imports.append(f"from .{edge_filename} import {edge_base_name}")

            mapped_type = "UUID | None" if field.nullable else "UUID"
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += "mapped_column(DBUUID(as_uuid=True), "
            fields_code += f'ForeignKey("{_get_table_name(edge_base_name)}.id")'
            fields_code += f"{common_column_attributes})\n"
        else:
            raise Exception(f"Unsupported field type: {type(field)}")

    return GeneratedContent(
        imports=[
            "from sqlalchemy import ForeignKey, String",
            "from sqlalchemy.orm import Mapped, mapped_column",
            "from sqlalchemy.dialects.postgresql import UUID as DBUUID",
        ]
        + edges_imports,
        code=f"""
class {base_name}Model(EntModel):
    __tablename__ = "{_get_table_name(base_name)}"

{fields_code}
""",
    )


def _get_table_name(base_name: str) -> str:
    # Remove "Ent" prefix
    if base_name.startswith("Ent"):
        base_name = base_name[3:]

    # Convert CamelCase to snake_case
    # Insert underscore before uppercase letters (except first)
    base_name = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name)

    # Convert to lowercase
    return base_name.lower()
