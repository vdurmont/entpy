from entpy import (
    BoolField,
    DatetimeField,
    EdgeField,
    EnumField,
    IntField,
    JsonField,
    StringField,
    TextField,
)
from entpy.framework.fields.core import FieldWithDefault
from entpy.framework.pattern import Pattern
from entpy.framework.schema import Schema
from entpy.gencode.generated_content import GeneratedContent
from entpy.gencode.utils import to_snake_case


def generate(
    pattern_class: type[Pattern],
    children_schema_classes: list[type[Schema]],
    base_import: str,
) -> str:
    pattern = pattern_class()
    base_name = pattern_class.__name__.replace("Pattern", "")
    schemas = [s() for s in children_schema_classes]
    print(f"I got {len(schemas)} schemas")

    selects = ""
    imports = []
    for schema in schemas:
        schema_base_name = schema.__class__.__name__.replace("Schema", "")
        imports.append(
            f"from .{to_snake_case(schema_base_name)} import {schema_base_name}Model"
        )
        fields_code = ""
        for field in pattern.get_all_fields():
            fields_code += f"{schema_base_name}Model.{field.name},"
        selects += f"""    select(
        literal_column("'{schema_base_name}Model'").label("ent_type"),
        {schema_base_name}Model.id,
        {schema_base_name}Model.created_at,
        {schema_base_name}Model.updated_at,
        {fields_code}
    ),
"""

    columns = _generate_columns(pattern=pattern)
    imports += columns.imports

    imports_code = "\n".join(sorted(set(imports)))

    # Generate column accessors for the view
    column_accessors = ""
    standard_fields = ["id", "created_at", "updated_at", "ent_type"]
    for field_name in standard_fields:
        column_accessors += f"\n    {field_name} = __table__.c.{field_name}"
    for field in pattern.get_all_fields():
        column_accessors += f"\n    {field.name} = __table__.c.{field.name}"

    return f"""
from sqlalchemy import (
    DDL,
    Column,
    MetaData,
    Table,
    event,
    literal_column,
    select,
    union_all,
    Selectable,
)
from entpy.framework.view import create_view
{imports_code}

{base_import}


view_query: Selectable = union_all(
{selects}
)

class {base_name}View(Base):
    __table__: Table = create_view(
        "{to_snake_case(base_name)}_view",
        view_query,
        metadata=Base.metadata,
    )
"""  # noqa: E501


def _generate_columns(pattern: Pattern) -> GeneratedContent:
    imports = [
        "from entpy.types import DateTime",
        "from sqlalchemy import String, UUID as DBUUID",
    ]
    code = ""
    for field in pattern.get_all_fields():
        common_column_attributes = ", nullable=" + (
            "True" if field.nullable else "False"
        )
        common_column_attributes += ", unique=True" if field.is_unique else ""
        if isinstance(field, FieldWithDefault):
            default = field.generate_default()
            if default:
                common_column_attributes += f", server_default={default}"
        if isinstance(field, DatetimeField):
            column_type = "DateTime()"
        elif isinstance(field, BoolField):
            column_type = "Boolean()"
        elif isinstance(field, EdgeField):
            column_type = "DBUUID()"
        elif isinstance(field, EnumField):
            module = field.enum_class.__module__
            type_name = field.enum_class.__name__
            imports.append("from sqlalchemy import Enum as DBEnum")
            imports.append(f"from {module} import {type_name}")
            column_type = f"DBEnum({type_name}, native_enum=True)"
        elif isinstance(field, IntField):
            imports.append("from sqlalchemy import Integer")
            column_type = "Integer()"
        elif isinstance(field, JsonField):
            imports.append("from sqlalchemy import JSON")
            column_type = "JSON()"
        elif isinstance(field, StringField):
            imports.append("from sqlalchemy import String")
            column_type = f"String({field.length})"
        elif isinstance(field, TextField):
            imports.append("from sqlalchemy import Text")
            column_type = "Text()"
        else:
            raise Exception(f"Unsupported field type: {type(field)}")

        code += f"""        Column("{field.name}", {column_type}{common_column_attributes}),"""  # noqa: E501
    return GeneratedContent(
        imports=imports,
        code=f"""
        Column("id", DBUUID(), primary_key=True),
        Column("created_at", DateTime()),
        Column("updated_at", DateTime()),
        Column("ent_type", String(50)),
{code}""",
    )
