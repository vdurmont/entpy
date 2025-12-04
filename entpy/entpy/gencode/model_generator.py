import re

from entpy import (
    BoolField,
    CompositeIndex,
    DatetimeField,
    EdgeField,
    EnumField,
    IntField,
    JsonField,
    Pattern,
    Schema,
    StringField,
    TextField,
)
from entpy.framework.descriptor import Descriptor
from entpy.framework.fields.core import FieldWithDefault
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(descriptor: Descriptor, base_name: str) -> GeneratedContent:
    # Only use the fields for this specific descriptor. The patterns fields will
    # be handled by inheritance.
    fields = descriptor.get_sorted_fields()

    fields_code = ""
    types_imports = []
    for field in fields:
        common_column_attributes = ", nullable=" + (
            "True" if field.nullable else "False"
        )
        common_column_attributes += ", unique=True" if field.is_unique else ""
        common_column_attributes += ", index=True" if field.is_indexed else ""
        if isinstance(field, FieldWithDefault):
            default = field.generate_default()
            if default:
                common_column_attributes += f", server_default={default}"

        mapped_type = (
            field.get_python_type() + " | None"
            if field.nullable
            else field.get_python_type()
        )

        if isinstance(field, BoolField):
            types_imports.append("from sqlalchemy import Boolean")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(Boolean(){common_column_attributes})\n"
        elif isinstance(field, DatetimeField):
            types_imports.append("from entpy.types import DateTime")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f"mapped_column(DateTime(){common_column_attributes})\n"
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
            types_imports.append("from sqlalchemy.dialects.postgresql import JSONB")
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += f'mapped_column(JSON().with_variant(JSONB(), "postgresql"){common_column_attributes})\n'
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
            edge_base_name = field.edge_class.__name__.replace("Schema", "").replace(
                "Pattern", ""
            )
            fields_code += f"    {field.name}: Mapped[{mapped_type}] = "
            fields_code += "mapped_column(DBUUID()"
            if not field.edge_class.__name__.endswith("Pattern"):
                # Cannot do FKs for Patterns
                fields_code += f', ForeignKey("{_get_table_name(edge_base_name)}.id")'
            fields_code += f"{common_column_attributes})\n"
        else:
            raise Exception(f"Unsupported field type: {type(field)}")

    indexes = (
        _generate_indexes(schema=descriptor, base_name=base_name)
        if isinstance(descriptor, Schema)
        else GeneratedContent("")
    )

    metadata = (
        "__abstract__ = True"
        if isinstance(descriptor, Pattern)
        else f'__tablename__ = "{_get_table_name(base_name)}"'
    )

    extends = _generate_extends(descriptor=descriptor)

    return GeneratedContent(
        imports=[
            "from sqlalchemy.orm import Mapped, mapped_column",
            "from sqlalchemy import UUID as DBUUID",
        ]
        + types_imports
        + indexes.imports
        + extends.imports,
        code=f"""
class {base_name}Model({extends.code}):
    {metadata}

{fields_code}

{indexes.code}
""",
    )


def _generate_indexes(schema: Schema, base_name: str) -> GeneratedContent:
    indexes = schema.get_composite_indexes()
    return GeneratedContent(
        imports=["from sqlalchemy import Index"] if indexes else [],
        code="\n".join(
            [_generate_index(index=index, base_name=base_name) for index in indexes]
        ),
    )


def _generate_index(index: CompositeIndex, base_name: str) -> str:
    return f"""Index(
    "{index.name}",
{"\n".join([f"    {base_name}Model.{field_name}," for field_name in index.field_names])}
{"    unique = True" if index.unique else ""}
)"""


def _get_table_name(base_name: str) -> str:
    # Remove "Ent" prefix
    if base_name.startswith("Ent"):
        base_name = base_name[3:]

    # Convert CamelCase to snake_case
    # Insert underscore before uppercase letters (except first)
    base_name = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name)

    # Convert to lowercase
    return base_name.lower()


def _generate_extends(descriptor: Descriptor) -> GeneratedContent:
    patterns = descriptor.get_patterns()
    code = ", ".join(
        [p.__class__.__name__.replace("Pattern", "") + "Model" for p in patterns]
    )

    def get_import(pattern: Pattern) -> str:
        base_name = pattern.__class__.__name__.replace("Pattern", "")
        return f"from .{to_snake_case(base_name)} import {base_name}Model"

    imports = [get_import(p) for p in patterns]
    return (
        GeneratedContent(code=code, imports=imports)
        if code
        else GeneratedContent(code="EntModel")
    )
