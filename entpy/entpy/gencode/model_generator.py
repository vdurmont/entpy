import re

from entpy import (
    DatetimeField,
    EdgeField,
    EnumField,
    IntField,
    JsonField,
    Schema,
    StringField,
    TextField,
)
from entpy.framework.fields.core import FieldWithDefault
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(schema: Schema, base_name: str) -> GeneratedContent:
    fields = schema.get_all_fields()

    fields_code = ""
    edges_imports = []
    types_imports = []
    for field in fields:
        common_column_attributes = ", nullable=" + (
            "True" if field.nullable else "False"
        )
        common_column_attributes += ", unique=True" if field.is_unique else ""
        if isinstance(field, FieldWithDefault):
            default = field.generate_default()
            if default:
                common_column_attributes += f", server_default={default}"

        mapped_type = (
            field.get_python_type() + " | None"
            if field.nullable
            else field.get_python_type()
        )

        if isinstance(field, DatetimeField):
            types_imports.append("from sqlalchemy import DateTime")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += (
                f"mapped_column(DateTime(timezone=True){common_column_attributes})\n"
            )
        elif isinstance(field, EnumField):
            module = field.enum_class.__module__
            type_name = field.enum_class.__name__
            types_imports.append("from sqlalchemy import Enum as DBEnum")
            types_imports.append(f"from {module} import {type_name}")
            mapped_type = type_name + " | None" if field.nullable else type_name
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(DBEnum({type_name}, native_enum=True)"
            fields_code += f"{common_column_attributes})\n"
        elif isinstance(field, IntField):
            types_imports.append("from sqlalchemy import Integer")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Integer(){common_column_attributes})\n"
        elif isinstance(field, JsonField):
            types_imports.append("from sqlalchemy import JSON")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(JSON(){common_column_attributes})\n"
        elif isinstance(field, StringField):
            types_imports.append("from sqlalchemy import String")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += (
                f"mapped_column(String({field.length}){common_column_attributes})\n"
            )
        elif isinstance(field, TextField):
            types_imports.append("from sqlalchemy import Text")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Text(){common_column_attributes})\n"
        elif isinstance(field, EdgeField):
            types_imports.append("from sqlalchemy import ForeignKey")
            edge_base_name = field.edge_class.__name__.replace("Schema", "")
            edge_filename = to_snake_case(edge_base_name)
            if edge_base_name != base_name:
                edges_imports.append(f"from .{edge_filename} import {edge_base_name}")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += "mapped_column(DBUUID(as_uuid=True), "
            fields_code += f'ForeignKey("{_get_table_name(edge_base_name)}.id")'
            fields_code += f"{common_column_attributes})\n"
        else:
            raise Exception(f"Unsupported field type: {type(field)}")

    return GeneratedContent(
        imports=[
            "from sqlalchemy.orm import Mapped, mapped_column",
            "from sqlalchemy.dialects.postgresql import UUID as DBUUID",
        ]
        + types_imports
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
